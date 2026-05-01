"""
Batch API version of baseline.

Usage:
  python run_baseline_batch.py submit    # prepare & submit batch
  python run_baseline_batch.py retrieve  # check status & save results
"""

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from db_client import get_database_schema, DB_ID
from utils import render_prompt

load_dotenv()

RESULTS_DIR = os.path.join("results", "baseline")
TEST_PATH = "test.json"
OUTPUT_PATH = os.path.join(RESULTS_DIR, "results.json")
BATCH_STATE_PATH = os.path.join(RESULTS_DIR, "batch_state.json")
BATCH_INPUT_PATH = os.path.join(RESULTS_DIR, "batch_input.jsonl")
TEMPLATE_PATH = os.path.join("baseline", "templates", "prompt.md")


def submit():
    with open(TEST_PATH, encoding="utf-8") as f:
        samples = json.load(f)

    model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    requests = []
    skipped = 0

    print(f"Preparing {len(samples)} requests...")

    for sample in samples:
        item_id = sample["id"]
        db_id = sample["db_id"]
        user_request = sample["user_request"]

        try:
            schema_context = get_database_schema(DB_ID(db_id))
            prompt = render_prompt(TEMPLATE_PATH, schema=schema_context, user_input=user_request)
            requests.append({
                "custom_id": str(item_id),
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0,
                },
            })
        except Exception as e:
            print(f"[{item_id}] ERROR preparing: {e}")
            skipped += 1

    print(f"Prepared {len(requests)} requests, skipped {skipped}")

    os.makedirs(RESULTS_DIR, exist_ok=True)

    with open(BATCH_INPUT_PATH, "w", encoding="utf-8") as f:
        for req in requests:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print("Uploading batch input file...")
    with open(BATCH_INPUT_PATH, "rb") as f:
        batch_file = client.files.create(file=f, purpose="batch")

    print("Creating batch job...")
    batch = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )

    state = {"batch_id": batch.id, "file_id": batch_file.id, "total": len(requests)}
    with open(BATCH_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print(f"\nBatch submitted!")
    print(f"  batch_id : {batch.id}")
    print(f"  status   : {batch.status}")
    print(f"  state    : {BATCH_STATE_PATH}")
    print(f"\nRun 'retrieve' later to check status and save results.")


def retrieve():
    if not os.path.exists(BATCH_STATE_PATH):
        print("No batch state found. Run 'submit' first.")
        return

    with open(BATCH_STATE_PATH, encoding="utf-8") as f:
        state = json.load(f)

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    batch = client.batches.retrieve(state["batch_id"])

    counts = batch.request_counts
    print(f"Batch ID : {batch.id}")
    print(f"Status   : {batch.status}")
    print(f"Progress : {counts.completed} completed, {counts.failed} failed / {counts.total} total")

    if batch.status != "completed":
        print("Batch not ready yet. Try again later.")
        return

    print("Downloading results...")
    content = client.files.content(batch.output_file_id)

    with open(TEST_PATH, encoding="utf-8") as f:
        samples_by_id = {str(s["id"]): s for s in json.load(f)}

    results = []
    n_ok = n_err = 0

    for line in content.text.strip().splitlines():
        resp = json.loads(line)
        custom_id = resp["custom_id"]
        sample = samples_by_id.get(custom_id)
        item_id = sample["id"] if sample else custom_id
        db_id = sample["db_id"] if sample else ""

        if resp.get("error"):
            results.append({"id": item_id, "db_id": db_id, "error": resp["error"]["message"]})
            n_err += 1
            continue

        try:
            raw = resp["response"]["body"]["choices"][0]["message"]["content"]
            sqls = json.loads(raw)["sqls"]
            results.append({"id": item_id, "db_id": db_id, "sqls": sqls})
            n_ok += 1
        except Exception as e:
            results.append({"id": item_id, "db_id": db_id, "error": str(e)})
            n_err += 1

    results.sort(key=lambda x: x["id"])

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDone: {n_ok} OK, {n_err} errors")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "submit":
        submit()
    elif cmd == "retrieve":
        retrieve()
    else:
        print("Usage: python run_baseline_batch.py [submit|retrieve]")

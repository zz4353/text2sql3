"""
Batch API version of run_extract_values_pipeline1.py (50% cheaper, async).

Usage:
  python run_extract_values_pipeline1_batch.py submit    # prepare & submit batch
  python run_extract_values_pipeline1_batch.py retrieve  # check status & save results
"""

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from db_client import get_llm_table_schema_context, DB_ID
from pipeline1.extract_values import _build_examples, _strip_samples, _parse_llm_records
from utils import render_prompt

load_dotenv()

RESULTS_DIR = os.path.join("results", "pipeline1")
SELECT_COLUMNS_PATH = os.path.join(RESULTS_DIR, "selected_cols.json")
OUTPUT_PATH = os.path.join(RESULTS_DIR, "extracted_values.json")
TEST_PATH = "test.json"
BATCH_STATE_PATH = os.path.join(RESULTS_DIR, "batch_state.json")
BATCH_INPUT_PATH = os.path.join(RESULTS_DIR, "batch_input.jsonl")
TEMPLATE_PATH = os.path.join("pipeline1", "templates", "extract_values.md")


def _build_prompt(user_request: str, selected_columns: dict, schema_context: list) -> str:
    examples = _build_examples(selected_columns, schema_context)
    schema_context_stripped = _strip_samples(schema_context)
    return render_prompt(
        TEMPLATE_PATH,
        user_input=user_request,
        column_descriptions=schema_context_stripped,
        columns=selected_columns,
        examples=examples,
    )


def submit():
    with open(SELECT_COLUMNS_PATH, encoding="utf-8") as f:
        select_columns_data = json.load(f)
    with open(TEST_PATH, encoding="utf-8") as f:
        test_lookup = {s["id"]: s for s in json.load(f)}

    samples = [s for s in select_columns_data if "error" not in s]
    print(f"Preparing {len(samples)} requests...")

    model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    requests = []
    skipped = 0

    for sample in samples:
        item_id = sample["id"]
        db_id = sample["db_id"]
        selected_columns = sample["selected_columns"]

        test_sample = test_lookup.get(item_id)
        if test_sample is None:
            print(f"[{item_id}] SKIP: not found in test.json")
            skipped += 1
            continue

        try:
            full_schema = get_llm_table_schema_context(DB_ID(db_id))
            selected_set = {
                f"{table}.{col}"
                for table, cols in selected_columns.items()
                for col in cols
            }
            schema_context = [
                sc for sc in full_schema
                if sc["original_column_name"] in selected_set
            ]
            prompt = _build_prompt(test_sample["user_request"], selected_columns, schema_context)
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

    with open(SELECT_COLUMNS_PATH, encoding="utf-8") as f:
        select_columns_data = json.load(f)
    samples_by_id = {str(s["id"]): s for s in select_columns_data if "error" not in s}

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
            llm_result = json.loads(raw)
            parsed = _parse_llm_records(llm_result, sample["selected_columns"])
            results.append({"id": item_id, "db_id": db_id, "extract_values": parsed})
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
        print("Usage: python run_extract_values_pipeline1_batch.py [submit|retrieve]")

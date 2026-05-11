"""
Batch API version of pipeline4 select_columns step.

Usage:
  python run_select_columns_pipeline_batch.py submit    # prepare & submit batch
  python run_select_columns_pipeline_batch.py retrieve  # check status & save results
"""

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from db_client import get_llm_table_schema_context, get_all_foreign_keys, DB_ID
from db_client import get_all_table_column_names2
from pipeline4.select_columns import _map_to_valid_columns, _apply_column_constraints, _format_schema
from utils import render_prompt, extract_columns_from_insert
from utils.text_to_image import render_text_pages_b64

load_dotenv()

RESULTS_DIR = os.path.join("results", "pipeline4")
TEST_PATH = "test.json"
OUTPUT_PATH = os.path.join(RESULTS_DIR, "selected_cols.json")
BATCH_STATE_PATH = os.path.join(RESULTS_DIR, "select_cols_batch_state.json")
BATCH_INPUT_PATH = os.path.join(RESULTS_DIR, "select_cols_batch_input.jsonl")
TEMPLATE_PATH = os.path.join("pipeline4", "templates", "select_cols.md")


def submit():
    with open(TEST_PATH, encoding="utf-8") as f:
        samples = json.load(f)

    model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    requests = []
    skipped = 0

    print(f"Preparing {len(samples)} requests...")

    samples = samples[:5]

    for sample in samples:
        item_id = sample["id"]
        db_id = sample["db_id"]
        user_input = sample["user_request"]

        try:
            schema_context = get_llm_table_schema_context(DB_ID(db_id))
            foreign_keys = get_all_foreign_keys(DB_ID(db_id))
            system_prompt = render_prompt(TEMPLATE_PATH, foreign_keys=foreign_keys)

            schema_images = render_text_pages_b64(_format_schema(schema_context), header="[Database Schema]")
            user_input_images = render_text_pages_b64(str(user_input), header="[User Request]")
            all_images = schema_images + user_input_images

            user_content = [
                {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"}
                for b64 in all_images
            ]
            requests.append({
                "custom_id": str(item_id),
                "method": "POST",
                "url": "/v1/responses",
                "body": {
                    "model": model,
                    "input": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "text": {"format": {"type": "json_object"}},
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
        endpoint="/v1/responses",
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
    lines = client.files.content(batch.output_file_id).text.strip().splitlines()
    if batch.error_file_id:
        lines += client.files.content(batch.error_file_id).text.strip().splitlines()

    with open(TEST_PATH, encoding="utf-8") as f:
        samples_by_id = {str(s["id"]): s for s in json.load(f)}

    results = []
    n_ok = n_err = 0

    for line in lines:
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
            raw = resp["response"]["body"]["output"][0]["content"][0]["text"]
            raw_cols = extract_columns_from_insert(json.loads(raw)["sql"])

            all_columns = get_all_table_column_names2(DB_ID(db_id))
            valid_cols = _map_to_valid_columns(raw_cols, all_columns)
            selected_columns = _apply_column_constraints(DB_ID(db_id), valid_cols)

            results.append({"id": item_id, "db_id": db_id, "selected_columns": selected_columns})
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
        print("Usage: python run_select_columns_pipeline_batch.py [submit|retrieve]")

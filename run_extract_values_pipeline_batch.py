"""
Batch API version of pipeline4 extract_values step.

Usage:
  python run_extract_values_pipeline_batch.py submit    # prepare & submit batch
  python run_extract_values_pipeline_batch.py retrieve  # check status & save results
"""

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from db_client import get_llm_table_schema_context, DB_ID
from pipeline4.extract_values import _build_examples, _strip_samples, _parse_llm_records, _format_column_descriptions
from utils import render_prompt
from utils.text_to_image import render_text_pages_b64

load_dotenv()

RESULTS_DIR = os.path.join("results", "pipeline4")
SELECT_COLUMNS_PATH = os.path.join(RESULTS_DIR, "selected_cols.json")
OUTPUT_PATH = os.path.join(RESULTS_DIR, "extracted_values.json")
TEST_PATH = "test.json"
BATCH_STATE_PATH = os.path.join(RESULTS_DIR, "extract_values_batch_state.json")
BATCH_INPUT_PATH = os.path.join(RESULTS_DIR, "extract_values_batch_input.jsonl")
TEMPLATE_PATH = os.path.join("pipeline4", "templates", "extract_values.md")


def _build_request_body(model: str, user_request: str, selected_columns: dict, schema_context: list) -> dict:
    examples = _build_examples(selected_columns, schema_context)
    schema_context_stripped = _strip_samples(schema_context)
    system_prompt = render_prompt(TEMPLATE_PATH, columns=selected_columns, examples=examples)

    schema_text = _format_column_descriptions(schema_context_stripped)
    schema_images = render_text_pages_b64(schema_text, header="[Column Descriptions]")
    user_input_images = render_text_pages_b64(str(user_request), header="[User Request]")
    all_images = schema_images + user_input_images

    user_content = [
        {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"}
        for b64 in all_images
    ]
    return {
        "model": model,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "text": {"format": {"type": "json_object"}},
        "temperature": 0,
        "max_output_tokens": 32768,
    }


def submit():
    with open(SELECT_COLUMNS_PATH, encoding="utf-8") as f:
        select_columns_data = json.load(f)
    with open(TEST_PATH, encoding="utf-8") as f:
        test_lookup = {s["id"]: s for s in json.load(f)}

    samples = [s for s in select_columns_data if "error" not in s]
    samples = samples[:10]
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
            body = _build_request_body(model, test_sample["user_request"], selected_columns, schema_context)
            requests.append({
                "custom_id": str(item_id),
                "method": "POST",
                "url": "/v1/responses",
                "body": body,
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
            raw = resp["response"]["body"]["output"][0]["content"][0]["text"]
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
        print("Usage: python run_extract_values_pipeline_batch.py [submit|retrieve]")

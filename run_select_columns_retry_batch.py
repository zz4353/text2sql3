"""
Batch API version of pipeline4 select_columns step — retry only incorrect samples.

Loads IDs from selected_cols_incorrect.json, filters test.json to those IDs only,
then runs the same pipeline as run_select_columns_pipeline_batch.py.

Usage:
  python run_select_columns_retry_batch.py submit    # prepare & submit batch
  python run_select_columns_retry_batch.py upload    # upload existing JSONL (chunked)
  python run_select_columns_retry_batch.py retrieve  # check status & save results
"""

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from db_client import get_llm_table_schema_context, get_all_foreign_keys, DB_ID
from db_client import get_all_table_column_names2
from pipeline4.select_columns import _map_to_valid_columns, _apply_column_constraints, _format_schema, _format_foreign_keys
from utils import render_prompt, extract_columns_from_insert
from utils.text_to_image import render_text_pages_b64

load_dotenv()

RESULTS_DIR = os.path.join("results", "pipeline4")
TEST_PATH = "test.json"
INCORRECT_PATH = os.path.join(RESULTS_DIR, "selected_cols_incorrect.json")
OUTPUT_PATH = os.path.join(RESULTS_DIR, "selected_cols_retry.json")
BATCH_STATE_PATH = os.path.join(RESULTS_DIR, "select_cols_retry_batch_state.json")
BATCH_INPUT_PATH = os.path.join(RESULTS_DIR, "select_cols_retry_batch_input.jsonl")
TEMPLATE_PATH = os.path.join("pipeline4", "templates", "select_cols.md")
CHUNK_SIZE = 50  # requests per batch chunk


def _upload_chunks(client, lines: list[str]) -> list[dict]:
    """Split lines into chunks, upload each, return list of batch info dicts."""
    chunks = [lines[i:i + CHUNK_SIZE] for i in range(0, len(lines), CHUNK_SIZE)]
    batches = []
    for idx, chunk in enumerate(chunks):
        chunk_path = BATCH_INPUT_PATH + f".chunk{idx}.jsonl"
        with open(chunk_path, "w", encoding="utf-8") as f:
            f.write("\n".join(chunk))
        print(f"  Uploading chunk {idx + 1}/{len(chunks)} ({len(chunk)} requests)...")
        with open(chunk_path, "rb") as f:
            batch_file = client.files.create(file=f, purpose="batch")
        batch = client.batches.create(
            input_file_id=batch_file.id,
            endpoint="/v1/responses",
            completion_window="24h",
        )
        batches.append({"batch_id": batch.id, "file_id": batch_file.id, "count": len(chunk)})
        print(f"    batch_id: {batch.id}  status: {batch.status}")
    return batches


def submit():
    with open(TEST_PATH, encoding="utf-8") as f:
        all_samples = {s["id"]: s for s in json.load(f)}

    with open(INCORRECT_PATH, encoding="utf-8") as f:
        incorrect_ids = {s["id"] for s in json.load(f)}

    samples = [s for s in all_samples.values() if s["id"] in incorrect_ids]
    print(f"Incorrect IDs to retry: {len(incorrect_ids)}, matched in test.json: {len(samples)}")

    model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    requests = []
    skipped = 0

    for sample in samples:
        item_id = sample["id"]
        db_id = sample["db_id"]
        user_input = sample["user_request"]

        try:
            schema_context = get_llm_table_schema_context(DB_ID(db_id))
            foreign_keys = get_all_foreign_keys(DB_ID(db_id))
            system_prompt = render_prompt(TEMPLATE_PATH)

            schema_images = render_text_pages_b64(_format_schema(schema_context), header="[Database Schema]")
            fk_images = render_text_pages_b64(_format_foreign_keys(foreign_keys), header="[Foreign Keys]")
            user_input_images = render_text_pages_b64(str(user_input), header="[User Request]")
            all_images = schema_images + fk_images + user_input_images

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

    lines = [json.dumps(req, ensure_ascii=False) for req in requests]
    print(f"Total requests: {len(lines)}, chunk size: {CHUNK_SIZE} → {-(-len(lines)//CHUNK_SIZE)} batches")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    batches = _upload_chunks(client, lines)

    state = {"batches": batches, "total": len(lines)}
    with open(BATCH_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print(f"\nAll chunks submitted! State saved: {BATCH_STATE_PATH}")
    print(f"Run 'retrieve' later to check status and save results.")


def retrieve():
    if not os.path.exists(BATCH_STATE_PATH):
        print("No batch state found. Run 'submit' or 'upload' first.")
        return

    with open(BATCH_STATE_PATH, encoding="utf-8") as f:
        state = json.load(f)

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    batch_list = state["batches"]

    all_lines = []
    all_done = True
    for b in batch_list:
        batch = client.batches.retrieve(b["batch_id"])
        counts = batch.request_counts
        print(f"[{batch.id}] {batch.status}  {counts.completed}/{counts.total} done, {counts.failed} failed")
        if batch.status != "completed":
            all_done = False
        else:
            lines = client.files.content(batch.output_file_id).text.strip().splitlines()
            all_lines.extend(lines)
            if batch.error_file_id:
                all_lines.extend(client.files.content(batch.error_file_id).text.strip().splitlines())

    if not all_done:
        print("\nSome batches not ready yet. Try again later.")
        return

    print("\nAll batches complete. Processing results...")
    with open(TEST_PATH, encoding="utf-8") as f:
        samples_by_id = {str(s["id"]): s for s in json.load(f)}

    results = []
    n_ok = n_err = 0

    for line in all_lines:
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


def upload():
    """Upload already-prepared JSONL (chunked) and create batch jobs."""
    if not os.path.exists(BATCH_INPUT_PATH):
        print(f"Batch input file not found: {BATCH_INPUT_PATH}")
        return

    with open(BATCH_INPUT_PATH, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    print(f"Total requests: {len(lines)}, chunk size: {CHUNK_SIZE} → {-(-len(lines)//CHUNK_SIZE)} batches")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    batches = _upload_chunks(client, lines)

    state = {"batches": batches, "total": len(lines)}
    with open(BATCH_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print(f"\nAll chunks submitted! State saved: {BATCH_STATE_PATH}")
    print(f"Run 'retrieve' later to check status and save results.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "submit":
        submit()
    elif cmd == "upload":
        upload()
    elif cmd == "retrieve":
        retrieve()
    else:
        print("Usage: python run_select_columns_retry_batch.py [submit|upload|retrieve]")

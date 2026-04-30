import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm_client import OpenAIClient
from pipeline1.extract_values import extract_values
from db_client import get_llm_table_schema_context, DB_ID

RESULTS_DIR = os.path.join("results", "pipeline1")
FAILED_PATH = os.path.join(RESULTS_DIR, "extracted_values_failed.json")
OUTPUT_PATH = os.path.join(RESULTS_DIR, "extracted_values.json")
TEST_PATH = "test.json"
MAX_WORKERS = 4

print_lock = threading.Lock()


def log(msg: str):
    with print_lock:
        print(msg)


def run_one(sample: dict, test_lookup: dict) -> dict:
    try:
        item_id = sample["id"]
        db_id = sample["db_id"]
        selected_columns = sample["selected_columns"]

        test_sample = test_lookup.get(item_id)
        if test_sample is None:
            return {"id": item_id, "db_id": db_id, "error": f"id={item_id} not found in test.json"}

        user_request = test_sample["user_request"]

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

        llm = OpenAIClient()
        result = extract_values(llm, user_request, selected_columns, schema_context)

        log(f"[{item_id}] OK — {len(result)} table group(s)")
        return {"id": item_id, "db_id": db_id, "extract_values": result}

    except Exception as e:
        log(f"[{item_id}] ERROR: {e}")
        return {"id": item_id, "db_id": db_id, "error": str(e)}


def main():
    with open(FAILED_PATH, encoding="utf-8") as f:
        samples = json.load(f)

    with open(TEST_PATH, encoding="utf-8") as f:
        test_lookup = {s["id"]: s for s in json.load(f)}

    print(f"Retrying {len(samples)} failed samples (workers={MAX_WORKERS})")

    retry_results = [None] * len(samples)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_idx = {
            executor.submit(run_one, sample, test_lookup): i
            for i, sample in enumerate(samples)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                retry_results[idx] = future.result()
            except Exception as e:
                sample = samples[idx]
                item_id = sample.get("id", f"idx={idx}")
                retry_results[idx] = {"id": item_id, "db_id": sample.get("db_id", ""), "error": str(e)}

    # Merge vào extracted_values.json
    with open(OUTPUT_PATH, encoding="utf-8") as f:
        existing = json.load(f)

    existing_by_id = {r["id"]: r for r in existing}
    for r in retry_results:
        if r is not None:
            existing_by_id[r["id"]] = r

    merged = sorted(existing_by_id.values(), key=lambda x: x["id"])

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    n_ok = sum(1 for r in retry_results if r and "error" not in r)
    n_err = sum(1 for r in retry_results if r and "error" in r)
    print(f"\nDone: {n_ok} OK, {n_err} errors")
    print(f"Merged into: {OUTPUT_PATH} ({len(merged)} total entries)")


if __name__ == "__main__":
    main()

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm_client import OpenAIClient
from pipeline1.extract_values import extract_values
from db_client import get_llm_table_schema_context, DB_ID

RESULTS_DIR = os.path.join("results", "pipeline1")
SELECT_COLUMNS_PATH = os.path.join(RESULTS_DIR, "selected_cols.json")
OUTPUT_PATH = os.path.join(RESULTS_DIR, "extracted_values.json")
LOG_PATH = os.path.join(RESULTS_DIR, "extracted_values_errors.log")
TEST_PATH = "test.json"
MAX_WORKERS = 8
SAVE_EVERY = 8

print_lock = threading.Lock()


def log(msg: str):
    with print_lock:
        print(msg)


def log_error(msg: str):
    with print_lock:
        print(msg)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")


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


def save_checkpoint(results: list):
    partial = sorted(
        [r for r in results if r is not None],
        key=lambda x: x["id"],
    )
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(partial, f, ensure_ascii=False, indent=2)
    return len(partial)


def main():
    with open(SELECT_COLUMNS_PATH, encoding="utf-8") as f:
        select_columns_data = json.load(f)

    with open(TEST_PATH, encoding="utf-8") as f:
        test_lookup = {s["id"]: s for s in json.load(f)}

    samples = [s for s in select_columns_data if "error" not in s][:4]
    print(f"Running extract_values on {len(samples)} samples (workers={MAX_WORKERS})")

    # Clear log file for this run
    open(LOG_PATH, "w", encoding="utf-8").close()

    results = [None] * len(samples)
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_idx = {
            executor.submit(run_one, sample, test_lookup): i
            for i, sample in enumerate(samples)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                sample = samples[idx]
                item_id = sample.get("id", f"idx={idx}")
                db_id = sample.get("db_id", "")
                msg = f"[{item_id}] CRASH: {e}"
                log_error(msg)
                results[idx] = {"id": item_id, "db_id": db_id, "error": f"CRASH: {e}"}

            completed += 1
            if completed % SAVE_EVERY == 0:
                n = save_checkpoint(results)
                log(f"[checkpoint] {completed}/{len(samples)} done — saved {n} results")

    save_checkpoint(results)

    n_ok = sum(1 for r in results if r is not None and "error" not in r)
    n_err = sum(1 for r in results if r is not None and "error" in r)
    print(f"\nDone: {n_ok} OK, {n_err} errors")
    print(f"Saved: {OUTPUT_PATH}")
    if n_err:
        print(f"Error log: {LOG_PATH}")


if __name__ == "__main__":
    main()

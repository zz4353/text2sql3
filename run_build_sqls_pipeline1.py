import json
import os

from db_client import DB_ID
from pipeline1.build_sqls import build_sqls

RESULTS_DIR = os.path.join("z", "gpt4.1")
INPUT_PATH = os.path.join(RESULTS_DIR, "extracted_values.json")
OUTPUT_PATH = os.path.join(RESULTS_DIR, "built_sqls.json")


def main():
    with open(INPUT_PATH, encoding="utf-8") as f:
        extracted_data = json.load(f)

    samples = [s for s in extracted_data if "error" not in s]
    upstream_errors = [s for s in extracted_data if "error" in s]
    print(f"Building SQLs for {len(samples)} samples (pass-through {len(upstream_errors)} upstream errors)")

    results = []
    n_ok = n_err = 0

    for sample in upstream_errors:
        results.append({"id": sample["id"], "db_id": sample["db_id"], "sqls": [], "error": sample["error"]})
        print(f"[{sample['id']}] UPSTREAM ERROR: {sample['error']}")

    for sample in samples:
        item_id = sample["id"]
        db_id = sample["db_id"]
        extract_values = sample["extract_values"]

        try:
            sqls = build_sqls(DB_ID(db_id), extract_values)
            built = [
                {"sql": sql, "params": params, "missing_required_columns": missing}
                for sql, params, missing in sqls
            ]
            results.append({"id": item_id, "db_id": db_id, "sqls": built})
            n_ok += 1
            print(f"[{item_id}] OK — {len(built)} statement(s)")
        except Exception as e:
            results.append({"id": item_id, "db_id": db_id, "error": str(e)})
            n_err += 1
            print(f"[{item_id}] ERROR: {e}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDone: {n_ok} OK, {n_err} errors")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

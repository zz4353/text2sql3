"""
Evaluate prediction results against gold SQLs.

Usage:
  python run_evaluation.py baseline
  python run_evaluation.py pipeline2
"""

import json
import os
import sys

from db_client import DB_ID
from evaluation import compare_sqls
from utils import render_sql_for_log

TEST_PATH = "test.json"

CONFIGS = {
    "baseline": {
        "input": os.path.join("results", "baseline", "results.json"),
        "output": os.path.join("results", "baseline", "evaluation.json"),
    },
    "pipeline2": {
        "input": os.path.join("results", "pipeline2", "built_sqls.json"),
        "output": os.path.join("results", "pipeline2", "evaluation.json"),
    },
}


def get_pred_sqls_baseline(sample: dict) -> list[str]:
    return sample.get("sqls", [])


def get_pred_sqls_pipeline2(sample: dict) -> list[str]:
    sqls = []
    for entry in sample.get("sqls", []):
        if entry.get("missing_required_columns"):
            continue
        sqls.append(render_sql_for_log(entry["sql"], entry["params"]))
    return sqls


def main(target: str):
    config = CONFIGS[target]

    with open(TEST_PATH, encoding="utf-8") as f:
        gold_lookup = {s["id"]: s for s in json.load(f)}

    with open(config["input"], encoding="utf-8") as f:
        predictions = json.load(f)

    get_pred_sqls = get_pred_sqls_baseline if target == "baseline" else get_pred_sqls_pipeline2

    samples = [s for s in predictions if "error" not in s]
    print(f"Evaluating {len(samples)} samples (skipped {len(predictions) - len(samples)} errors)")

    results = []
    n_correct = n_wrong = n_skip = 0

    for sample in samples:
        item_id = sample["id"]
        db_id = sample["db_id"]

        gold = gold_lookup.get(item_id)
        if gold is None:
            print(f"[{item_id}] SKIP: not found in test.json")
            n_skip += 1
            continue

        gold_sqls = gold["gold_sql"]
        pred_sqls = get_pred_sqls(sample)

        match, err = compare_sqls(gold_sqls, pred_sqls, DB_ID(db_id))

        results.append({
            "id": item_id,
            "db_id": db_id,
            "match": match,
            "error": err,
        })

        if match:
            n_correct += 1
        else:
            n_wrong += 1
            print(f"[{item_id}] WRONG: {err}")

    os.makedirs(os.path.dirname(config["output"]), exist_ok=True)
    with open(config["output"], "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total = n_correct + n_wrong
    accuracy = n_correct / total * 100 if total else 0
    print(f"\n=== {target} ===")
    print(f"Correct : {n_correct}/{total} ({accuracy:.1f}%)")
    print(f"Wrong   : {n_wrong}")
    if n_skip:
        print(f"Skipped : {n_skip}")
    print(f"Saved   : {config['output']}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CONFIGS:
        print(f"Usage: python run_evaluation.py [{' | '.join(CONFIGS)}]")
        sys.exit(1)
    main(sys.argv[1])

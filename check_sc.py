import json
from utils import extract_columns_from_insert

with open("test.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)
with open("results/pipeline4/selected_cols.json", "r", encoding="utf-8") as f:
    pred_data = json.load(f)

test_by_id = {s["id"]: s for s in test_data}
total = len(pred_data)
n_correct = 0

for p in pred_data:
    item_id = p["id"]
    if "error" in p:
        print(f"[{item_id}] ERROR")
        continue
    gold_cols = extract_columns_from_insert(test_by_id[item_id]["gold_sql"])
    pred_cols = p.get("selected_columns", {})
    gold_set = {f"{t}.{c}" for t, cols in gold_cols.items() for c in cols}
    pred_set = {f"{t}.{c}" for t, cols in pred_cols.items() for c in cols}
    ok = gold_set == pred_set
    if ok:
        n_correct += 1
    status = "OK  " if ok else "FAIL"
    print(f"[{item_id}] {status}  gold={sorted(gold_set)}")
    if not ok:
        print(f"         pred={sorted(pred_set)}")
        print(f"         miss={sorted(gold_set - pred_set)}")
        print(f"         extra={sorted(pred_set - gold_set)}")

print(f"\nCorrect: {n_correct}/{total} ({n_correct/total*100:.1f}%)")

"""Split pipeline4 selected_cols.json into correct and incorrect files."""
import json
from utils import extract_columns_from_insert

with open("test.json", "r", encoding="utf-8") as f:
    test_by_id = {s["id"]: s for s in json.load(f)}
with open("results/pipeline4/selected_cols.json", "r", encoding="utf-8") as f:
    pred_data = json.load(f)

correct = []
incorrect = []

for p in pred_data:
    item_id = p["id"]
    if "error" in p:
        incorrect.append(p)
        continue
    gold_cols = extract_columns_from_insert(test_by_id[item_id]["gold_sql"])
    gold_set = {f"{t}.{c}" for t, cols in gold_cols.items() for c in cols}
    pred_set = {f"{t}.{c}" for t, cols in p.get("selected_columns", {}).items() for c in cols}
    if gold_set == pred_set:
        correct.append(p)
    else:
        incorrect.append(p)

with open("results/pipeline4/selected_cols_correct.json", "w", encoding="utf-8") as f:
    json.dump(correct, f, ensure_ascii=False, indent=2)
with open("results/pipeline4/selected_cols_incorrect.json", "w", encoding="utf-8") as f:
    json.dump(incorrect, f, ensure_ascii=False, indent=2)

print(f"Correct  : {len(correct)} -> results/pipeline4/selected_cols_correct.json")
print(f"Incorrect: {len(incorrect)} -> results/pipeline4/selected_cols_incorrect.json")

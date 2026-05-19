import json
from utils import extract_columns_from_insert

with open("test.json", "r", encoding="utf-8") as f:
    test_by_id = {s["id"]: s for s in json.load(f)}
with open("results/pipeline4/selected_cols_retry.json", "r", encoding="utf-8") as f:
    pred_data = json.load(f)
with open("results/pipeline1/gpt4.1/selected_cols.json", "r", encoding="utf-8") as f:
    p1_data = {s["id"]: s for s in json.load(f)}

total = len(pred_data)
n_correct = n_wrong = n_err = 0

for p in pred_data:
    item_id = p["id"]
    if "error" in p:
        n_err += 1
        continue
    gold_cols = extract_columns_from_insert(test_by_id[item_id]["gold_sql"])
    gold_set = {f"{t}.{c}" for t, cols in gold_cols.items() for c in cols}
    pred_set = {f"{t}.{c}" for t, cols in p.get("selected_columns", {}).items() for c in cols}
    p1 = p1_data.get(item_id, {})
    p1_set = {f"{t}.{c}" for t, cols in p1.get("selected_columns", {}).items() for c in cols}

    ok = gold_set == pred_set
    status = "OK  " if ok else "FAIL"
    if ok:
        n_correct += 1
    else:
        n_wrong += 1
    miss = sorted(gold_set - pred_set)
    extra = sorted(pred_set - gold_set)
    p1_ok = p1_set == gold_set
    detail = ""
    if miss:
        detail += f"  miss={miss}"
    if extra:
        detail += f"  extra={extra}"
    p1_tag = "(p1:OK)" if p1_ok else "(p1:FAIL)"
    print(f"[{item_id}] {status} {p1_tag}{detail}")

print(f"\nRetry {total} câu: {n_correct} đúng ({n_correct/total*100:.1f}%), {n_wrong} sai, {n_err} lỗi")
print(f"So với lần trước (0/{total}): +{n_correct} câu đúng thêm")

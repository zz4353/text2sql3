"""Phân tích các câu sai của pipeline4 so với gold, so sánh với pipeline1."""
import json
from collections import defaultdict
from utils import extract_columns_from_insert

with open("test.json", "r", encoding="utf-8") as f:
    test_by_id = {s["id"]: s for s in json.load(f)}
with open("results/pipeline4/selected_cols.json", "r", encoding="utf-8") as f:
    p4_data = {s["id"]: s for s in json.load(f)}
with open("results/pipeline1/gpt4.1/selected_cols.json", "r", encoding="utf-8") as f:
    p1_data = {s["id"]: s for s in json.load(f)}

failures = []

for item_id, p4 in p4_data.items():
    if "error" in p4:
        continue
    gold_cols = extract_columns_from_insert(test_by_id[item_id]["gold_sql"])
    gold_set = {f"{t}.{c}" for t, cols in gold_cols.items() for c in cols}
    pred_set = {f"{t}.{c}" for t, cols in p4.get("selected_columns", {}).items() for c in cols}

    if gold_set == pred_set:
        continue

    missing = gold_set - pred_set
    extra = pred_set - gold_set

    p1 = p1_data.get(item_id, {})
    p1_set = {f"{t}.{c}" for t, cols in p1.get("selected_columns", {}).items() for c in cols}
    p1_ok = p1_set == gold_set

    failures.append({
        "id": item_id,
        "db_id": p4["db_id"],
        "missing": sorted(missing),
        "extra": sorted(extra),
        "p1_ok": p1_ok,
    })

n_total = len(p4_data)
n_fail = len(failures)
n_p1_correct_where_p4_fail = sum(1 for f in failures if f["p1_ok"])

print(f"Pipeline4: {n_total - n_fail}/{n_total} correct, {n_fail} failures\n")
print(f"Trong {n_fail} câu sai: pipeline1 đúng {n_p1_correct_where_p4_fail}, sai {n_fail - n_p1_correct_where_p4_fail}\n")

# Phân loại lỗi
only_missing = [f for f in failures if f["missing"] and not f["extra"]]
only_extra   = [f for f in failures if f["extra"] and not f["missing"]]
both         = [f for f in failures if f["missing"] and f["extra"]]

print(f"Loại lỗi:")
print(f"  Chỉ thiếu cột  : {len(only_missing)}")
print(f"  Chỉ thừa cột   : {len(only_extra)}")
print(f"  Vừa thiếu vừa thừa: {len(both)}")

# Tần suất cột bị thiếu nhiều nhất
miss_count = defaultdict(int)
extra_count = defaultdict(int)
for f in failures:
    for col in f["missing"]:
        miss_count[col] += 1
    for col in f["extra"]:
        extra_count[col] += 1

print(f"\nTop 15 cột bị THIẾU nhiều nhất:")
for col, cnt in sorted(miss_count.items(), key=lambda x: -x[1])[:15]:
    print(f"  {cnt:3d}x  {col}")

print(f"\nTop 15 cột bị THỪA nhiều nhất:")
for col, cnt in sorted(extra_count.items(), key=lambda x: -x[1])[:15]:
    print(f"  {cnt:3d}x  {col}")

# Câu sai mà pipeline1 đúng — có thể học được gì
print(f"\n--- Câu pipeline4 sai, pipeline1 đúng ({n_p1_correct_where_p4_fail} câu) ---")
for f in failures:
    if not f["p1_ok"]:
        continue
    miss_str = f"miss={f['missing']}" if f["missing"] else ""
    extra_str = f"extra={f['extra']}" if f["extra"] else ""
    print(f"  [{f['id']}] {f['db_id']}  {miss_str}  {extra_str}")

# Câu cả 2 đều sai
print(f"\n--- Câu cả pipeline4 và pipeline1 đều sai ({n_fail - n_p1_correct_where_p4_fail} câu) ---")
for f in failures:
    if f["p1_ok"]:
        continue
    miss_str = f"miss={f['missing']}" if f["missing"] else ""
    extra_str = f"extra={f['extra']}" if f["extra"] else ""
    print(f"  [{f['id']}] {f['db_id']}  {miss_str}  {extra_str}")

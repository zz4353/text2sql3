import json

with open("results/pipeline4/selected_cols.json", "r", encoding="utf-8") as f:
    p4 = {s["id"]: s.get("selected_columns", {}) for s in json.load(f)}

with open("results/pipeline1/gpt4.1/selected_cols.json", "r", encoding="utf-8") as f:
    p1 = {s["id"]: s.get("selected_columns", {}) for s in json.load(f)}

common_ids = sorted(set(p4) & set(p1))
n_same = n_diff = 0

for item_id in common_ids:
    s4 = {f"{t}.{c}" for t, cols in p4[item_id].items() for c in cols}
    s1 = {f"{t}.{c}" for t, cols in p1[item_id].items() for c in cols}
    if s4 == s1:
        n_same += 1
    else:
        n_diff += 1

total = len(common_ids)
print(f"Common samples : {total}")
print(f"Identical      : {n_same} ({n_same/total*100:.1f}%)")
print(f"Different      : {n_diff} ({n_diff/total*100:.1f}%)")

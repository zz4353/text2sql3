import json
import re


def extract_gold_columns(gold_sql_list: list[str]) -> dict[str, set[str]]:
    """Trích xuất {table: set(columns)} từ danh sách INSERT SQL."""
    result = {}
    for sql in gold_sql_list:
        m = re.match(
            r'INSERT\s+(?:OR\s+\w+\s+)?INTO\s+"?(\w+)"?\s*\(([^)]+)\)',
            sql.strip(), re.IGNORECASE
        )
        if not m:
            continue
        table = m.group(1).lower()
        cols = {c.strip().strip('"').lower() for c in m.group(2).split(',')}
        result.setdefault(table, set()).update(cols)
    return result


def is_correct(gold: dict[str, set[str]], predicted: dict[str, set[str]]) -> bool:
    """
    Dung khi:
    - Tap tables khop chinh xac (khong thua, khong thieu)
    - Voi moi table, tap columns khop chinh xac (khong thua, khong thieu)
    """
    gold_norm = {k.lower(): {c.lower() for c in v} for k, v in gold.items()}
    pred_norm = {k.lower(): {c.lower() for c in v} for k, v in predicted.items()}

    if set(gold_norm.keys()) != set(pred_norm.keys()):
        return False

    for table, gcols in gold_norm.items():
        if gcols != pred_norm[table]:
            return False

    return True


def main():
    with open("sstestok.json", encoding="utf-8") as f:
        test_data = {s["id"]: s for s in json.load(f)}

    with open("results_pipeline1_select_columns_by_id_sstestok.json", encoding="utf-8") as f:
        results = json.load(f)

    correct_samples = []
    wrong_samples = []

    for item in results:
        item_id = item["id"]
        test_sample = test_data[item_id]

        if "error" in item:
            wrong_samples.append({**item, "reason": "pipeline_error"})
            continue

        gold = extract_gold_columns(test_sample["gold_sql"])
        predicted = item["selected_columns"]

        if is_correct(gold, predicted):
            correct_samples.append({
                "id": item_id,
                "db_id": item["db_id"],
                "user_request": test_sample["user_request"],
                "gold_sql": test_sample["gold_sql"],
                "gold_columns": {t: sorted(cols) for t, cols in gold.items()},
                "selected_columns": predicted,
            })
        else:
            gold_norm = {k.lower(): {c.lower() for c in v} for k, v in gold.items()}
            pred_norm = {k.lower(): {c.lower() for c in v} for k, v in predicted.items()}
            all_tables = sorted(set(gold_norm) | set(pred_norm))
            table_diff = {}
            for t in all_tables:
                g = gold_norm.get(t, set())
                p = pred_norm.get(t, set())
                table_diff[t] = {
                    "gold": sorted(g),
                    "predicted": sorted(p),
                    "missing_cols": sorted(g - p),
                    "extra_cols": sorted(p - g),
                    "table_status": (
                        "missing_table" if t not in pred_norm
                        else "extra_table" if t not in gold_norm
                        else "ok"
                    ),
                }
            wrong_samples.append({
                "id": item_id,
                "db_id": item["db_id"],
                "user_request": test_sample["user_request"],
                "tables_missing": sorted(set(gold_norm) - set(pred_norm)),
                "tables_extra": sorted(set(pred_norm) - set(gold_norm)),
                "diff": table_diff,
            })

    correct_path = "results_pipeline1_select_columns_correct_sstestok.json"
    wrong_path = "results_pipeline1_select_columns_wrong_sstestok.json"

    with open(correct_path, "w", encoding="utf-8") as f:
        json.dump(correct_samples, f, ensure_ascii=False, indent=2)
    with open(wrong_path, "w", encoding="utf-8") as f:
        json.dump(wrong_samples, f, ensure_ascii=False, indent=2)

    total = len(results)
    n_correct = len(correct_samples)
    print(f"Total   : {total}")
    print(f"Correct : {n_correct}  ({n_correct/total*100:.1f}%)")
    print(f"Wrong   : {total - n_correct}  ({(total-n_correct)/total*100:.1f}%)")
    print(f"Saved   : {correct_path}")
    print(f"Saved   : {wrong_path}")

    print("\n--- Wrong samples (top 5) ---")
    for s in wrong_samples[:5]:
        if "reason" in s:
            print(f"  id={s['id']} ERROR: {s.get('error','')}")
            continue
        print(f"  id={s['id']} | tables_missing={s['tables_missing']} tables_extra={s['tables_extra']}")
        for t, d in s["diff"].items():
            if d["missing_cols"] or d["extra_cols"] or d["table_status"] != "ok":
                print(f"    {t}: missing={d['missing_cols']} extra={d['extra_cols']} [{d['table_status']}]")


if __name__ == "__main__":
    main()

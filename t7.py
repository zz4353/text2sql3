import json
import re


def extract_gold_columns(gold_sql_list: list[str]) -> dict[str, set[str]]:
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
    gold_norm = {k.lower(): {c.lower() for c in v} for k, v in gold.items()}
    pred_norm = {k.lower(): {c.lower() for c in v} for k, v in predicted.items()}
    if set(gold_norm.keys()) != set(pred_norm.keys()):
        return False
    for table, gcols in gold_norm.items():
        if gcols != pred_norm[table]:
            return False
    return True


def main():
    with open("test4.json", encoding="utf-8") as f:
        test_data = {s["id"]: s for s in json.load(f)}

    with open("selectcol4.json", encoding="utf-8") as f:
        results = json.load(f)

    wrong = []
    for item in results:
        item_id = item["id"]
        gold = extract_gold_columns(test_data[item_id]["gold_sql"])
        predicted = item["selected_columns"]
        if not is_correct(gold, predicted):
            wrong.append(item_id)

    total = len(results)
    n_correct = total - len(wrong)
    print(f"Total  : {total}")
    print(f"Correct: {n_correct} ({n_correct/total*100:.1f}%)")
    print(f"Wrong  : {len(wrong)}")
    if wrong:
        print(f"Wrong ids: {wrong[:20]}")


if __name__ == "__main__":
    main()

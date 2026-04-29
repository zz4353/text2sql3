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
    gn = {k.lower(): {c.lower() for c in v} for k, v in gold.items()}
    pn = {k.lower(): {c.lower() for c in v} for k, v in predicted.items()}
    return set(gn) == set(pn) and all(gn[t] == pn[t] for t in gn)


def main():
    with open("test.json", encoding="utf-8") as f:
        test_data = {s["id"]: s for s in json.load(f)}

    with open("results/pipeline1/selected_cols.json", encoding="utf-8") as f:
        results = json.load(f)

    correct_ids = []
    wrong_ids = []
    error_ids = []

    for item in results:
        iid = item["id"]
        if "error" in item:
            error_ids.append(iid)
        elif is_correct(
            extract_gold_columns(test_data[iid]["gold_sql"]),
            item["selected_columns"]
        ):
            correct_ids.append(iid)
        else:
            wrong_ids.append(iid)

    total = len(results)
    print(f"Correct: {len(correct_ids)} / {total}  ({len(correct_ids)/total*100:.1f}%)")
    print(f"Wrong  : {len(wrong_ids)}")
    print(f"Error  : {len(error_ids)}")
    print(f"\nWrong ids  : {wrong_ids}")
    if error_ids:
        print(f"Error ids  : {error_ids}")


if __name__ == "__main__":
    main()

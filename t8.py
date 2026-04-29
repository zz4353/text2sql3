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

    n_correct = sum(
        1 for item in results
        if "error" not in item
        and is_correct(
            extract_gold_columns(test_data[item["id"]]["gold_sql"]),
            item["selected_columns"]
        )
    )

    total = len(results)
    print(f"Correct: {n_correct} / {total}  ({n_correct/total*100:.1f}%)")


if __name__ == "__main__":
    main()

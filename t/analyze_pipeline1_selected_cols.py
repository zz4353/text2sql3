#!/usr/bin/env python3
"""Analyze pipeline1 selected-column results with fixed denominator 359."""

from __future__ import annotations

from pipeline1_common import (
    FIXED_TOTAL,
    TEXT2SQL_ROOT,
    extract_columns_from_insert,
    flatten_columns,
    fmt_pct,
    load_json,
    print_table,
    print_title,
)


MODELS = ["gpt4.1", "gpt4omini"]


def analyze_model(model: str) -> None:
    test_data = load_json(TEXT2SQL_ROOT / "test.json")
    test_by_id = {sample["id"]: sample for sample in test_data}

    path = TEXT2SQL_ROOT / "results" / "pipeline1" / model / "selected_cols.json"
    data = load_json(path)

    correct = only_missing = only_extra = both = errors = 0
    missing_entries = FIXED_TOTAL - len(data)

    for item in data:
        if "error" in item:
            errors += 1
            continue

        gold_sample = test_by_id[item["id"]]
        gold_columns = extract_columns_from_insert(gold_sample["gold_sql"])
        gold_set = flatten_columns(gold_columns)
        pred_set = flatten_columns(item.get("selected_columns", {}))

        if gold_set == pred_set:
            correct += 1
            continue

        missing = gold_set - pred_set
        extra = pred_set - gold_set
        if missing and extra:
            both += 1
        elif missing:
            only_missing += 1
        elif extra:
            only_extra += 1

    wrong_fixed = FIXED_TOTAL - correct

    print_title(f"PIPELINE1 - {model} - CHON BANG/COT")
    print_table(
        ["Chi so", "So luong", "Ty le theo 359"],
        [
            ["Dung hoan toan", correct, fmt_pct(correct)],
            ["Chi thieu cot", only_missing, fmt_pct(only_missing)],
            ["Chi thua cot", only_extra, fmt_pct(only_extra)],
            ["Vua thieu vua thua", both, fmt_pct(both)],
            ["Loi trong selected_cols", errors, fmt_pct(errors)],
            ["Thieu entry selected_cols", missing_entries, fmt_pct(missing_entries)],
            ["Tong sai theo mau so 359", wrong_fixed, fmt_pct(wrong_fixed)],
            ["Tong mau co dinh", FIXED_TOTAL, "100.00%"],
        ],
    )


def main() -> None:
    for model in MODELS:
        analyze_model(model)


if __name__ == "__main__":
    main()


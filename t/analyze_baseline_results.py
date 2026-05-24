#!/usr/bin/env python3
"""Analyze baseline evaluation results with fixed denominator 359."""

from __future__ import annotations

from collections import Counter, defaultdict

from baseline_common import (
    FIXED_TOTAL,
    TEXT2SQL_ROOT,
    fmt_pct,
    load_json,
    pct,
    print_table,
    print_title,
)


MODELS = ["gpt4.1", "gpt4omini"]


def classify_error(message: str | None) -> str:
    if not message:
        return "Khac"
    if "pred_sqls lỗi:" in message:
        if "UNIQUE constraint" in message:
            return "UNIQUE constraint"
        if "FOREIGN KEY constraint" in message:
            return "FOREIGN KEY constraint"
        if "NOT NULL constraint" in message:
            return "NOT NULL constraint"
        if "syntax error" in message:
            return "Syntax error"
        return "Other SQL error"
    if "khác values" in message:
        return "Sai gia tri"
    return "Khac"


def analyze_model(model: str) -> None:
    path = TEXT2SQL_ROOT / "results" / "baseline" / model / "evaluation.json"
    data = load_json(path)

    correct = sum(1 for item in data if item.get("match"))
    evaluated = len(data)
    missing = FIXED_TOTAL - evaluated
    wrong_in_file = evaluated - correct
    wrong_fixed = FIXED_TOTAL - correct

    print_title(f"BASELINE - {model} - TONG THE")
    print_table(
        ["Chi so", "Gia tri"],
        [
            ["File", path.relative_to(TEXT2SQL_ROOT)],
            ["Tong mau co dinh", FIXED_TOTAL],
            ["So mau trong evaluation.json", evaluated],
            ["So mau thieu trong evaluation.json", missing],
            ["So mau dung", correct],
            ["So mau sai trong file", wrong_in_file],
            ["So mau sai theo mau so 359", wrong_fixed],
            ["Do chinh xac theo 359", fmt_pct(correct)],
            ["Do chinh xac theo len(file)", f"{pct(correct, evaluated):.2f}%"],
        ],
    )

    by_db: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "correct": 0})
    for item in data:
        db_id = item["db_id"]
        by_db[db_id]["total"] += 1
        if item.get("match"):
            by_db[db_id]["correct"] += 1

    print_title(f"BASELINE - {model} - THEO CSDL")
    rows = []
    for db_id in sorted(by_db):
        total = by_db[db_id]["total"]
        correct_db = by_db[db_id]["correct"]
        rows.append([
            db_id,
            correct_db,
            total,
            total - correct_db,
            f"{pct(correct_db, total):.2f}%",
        ])
    print_table(["CSDL", "Dung", "Tong trong file", "Sai", "Do chinh xac"], rows)

    error_types = Counter()
    for item in data:
        if not item.get("match"):
            error_types[classify_error(item.get("error"))] += 1
    if missing > 0:
        error_types["Thieu evaluation"] += missing

    print_title(f"BASELINE - {model} - PHAN LOAI LOI")
    rows = [
        [error_type, count, f"{pct(count, wrong_fixed):.2f}% tren tong loi"]
        for error_type, count in error_types.most_common()
    ]
    print_table(["Loai loi", "So luong", "Ty le"], rows)


def main() -> None:
    for model in MODELS:
        analyze_model(model)


if __name__ == "__main__":
    main()


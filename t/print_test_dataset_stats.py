#!/usr/bin/env python3
"""Print dataset statistics for test.json."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PATH = REPO_ROOT / "test.json"


def pct(count: int, total: int) -> str:
    return f"{count / total * 100:.1f}" if total else "0.0"


def print_table(rows: list[list[object]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for index, row in enumerate(rows):
        line = "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        print(line)
        if index == 0:
            print("  ".join("-" * width for width in widths))


def main() -> None:
    with TEST_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)

    single_table = sum(1 for item in data if item["metadata"]["table_count"] == 1)
    multi_table = sum(1 for item in data if item["metadata"]["table_count"] >= 2)

    records_1_10 = sum(1 for item in data if 1 <= item["metadata"]["record_count"] <= 10)
    records_11_20 = sum(1 for item in data if 11 <= item["metadata"]["record_count"] <= 20)
    records_21_plus = sum(1 for item in data if item["metadata"]["record_count"] >= 21)

    rows = [
        ["Đặc điểm", "Số lượng", "Tỷ lệ (%)"],
        ["Theo độ phức tạp", "", ""],
        ["Single-table (1 bảng)", single_table, pct(single_table, total)],
        ["Multi-table (2+ bảng)", multi_table, pct(multi_table, total)],
        ["Theo số bản ghi", "", ""],
        ["1-10 bản ghi", records_1_10, pct(records_1_10, total)],
        ["11-20 bản ghi", records_11_20, pct(records_11_20, total)],
        ["21+ bản ghi", records_21_plus, pct(records_21_plus, total)],
        ["Tổng", total, pct(total, total)],
    ]

    print("Bảng 4.1. Thống kê bộ dữ liệu đánh giá 359 mẫu")
    print()
    print_table(rows)


if __name__ == "__main__":
    main()

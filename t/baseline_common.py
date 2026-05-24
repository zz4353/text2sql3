#!/usr/bin/env python3
"""Shared helpers for baseline report analysis."""

from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEXT2SQL_ROOT = REPO_ROOT
FIXED_TOTAL = 359


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def pct(count: int, total: int = FIXED_TOTAL) -> float:
    return count / total * 100 if total else 0.0


def fmt_pct(count: int, total: int = FIXED_TOTAL) -> str:
    return f"{pct(count, total):.2f}%"


def print_title(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_table(headers: list[str], rows: list[list[object]]) -> None:
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def render(row: list[object]) -> str:
        return " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))

    print(render(headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(render(row))


_IDENT = r'''(?:"[^"]+"|`[^`]+`|\[[^\]]+\]|'[^']+'|\w+)'''
_INSERT_COLS = re.compile(
    rf"INSERT\s+(?:OR\s+\w+\s+)?INTO\s+({_IDENT})\s*\(([^)]+)\)",
    re.IGNORECASE,
)


def unquote_identifier(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] in ('"', "`", "'") and value[-1] == value[0]:
        return value[1:-1]
    if len(value) >= 2 and value[0] == "[" and value[-1] == "]":
        return value[1:-1]
    return value


def extract_columns_from_insert(sqls: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for sql in sqls:
        match = _INSERT_COLS.search(sql)
        if not match:
            continue

        table = unquote_identifier(match.group(1))
        columns = [
            unquote_identifier(column)
            for column in match.group(2).split(",")
        ]
        result.setdefault(table, []).extend(columns)
    return result


def flatten_columns(selected_columns: dict[str, list[str]]) -> set[str]:
    return {
        f"{table}.{column}"
        for table, columns in selected_columns.items()
        for column in columns
    }


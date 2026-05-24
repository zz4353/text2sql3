#!/usr/bin/env python3
"""Run all pipeline2 analyses and print results to terminal."""

from __future__ import annotations

import analyze_pipeline2_results
import analyze_pipeline2_selected_cols


def main() -> None:
    analyze_pipeline2_results.main()
    analyze_pipeline2_selected_cols.main()


if __name__ == "__main__":
    main()


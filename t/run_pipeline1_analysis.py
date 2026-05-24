#!/usr/bin/env python3
"""Run all pipeline1 analyses and print results to terminal."""

from __future__ import annotations

import analyze_pipeline1_results
import analyze_pipeline1_selected_cols


def main() -> None:
    analyze_pipeline1_results.main()
    analyze_pipeline1_selected_cols.main()


if __name__ == "__main__":
    main()


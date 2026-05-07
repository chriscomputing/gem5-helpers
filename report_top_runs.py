# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from gem5_helpers import build_run_report, load_runs, sort_runs_by_stat


def _parse_comma_separated_list(raw_value: str, *, option_name: str) -> list[str]:
    values = [item.strip() for item in raw_value.split(",")]
    if not values or any(not value for value in values):
        raise argparse.ArgumentTypeError(
            f"{option_name} must be a comma-separated list of non-empty names"
        )
    return values


def _positive_int(raw_value: str) -> int:
    value = int(raw_value)
    if value <= 0:
        raise argparse.ArgumentTypeError("--top-n must be a positive integer")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report the top runs for a selected gem5 stat"
    )
    parser.add_argument(
        "parent_dir",
        type=Path,
        help="Directory containing gem5 run subdirectories",
    )
    parser.add_argument(
        "--stat",
        required=True,
        help="Stat name to rank runs by",
    )
    parser.add_argument(
        "--runs",
        type=lambda value: _parse_comma_separated_list(value, option_name="--runs"),
        help="Optional comma-separated run names to consider",
    )
    parser.add_argument(
        "--top-n",
        type=_positive_int,
        required=True,
        help="Number of ranked runs to report",
    )

    order_group = parser.add_mutually_exclusive_group()
    order_group.add_argument(
        "--desc",
        action="store_true",
        help="Sort with higher values first (default)",
    )
    order_group.add_argument(
        "--asc",
        action="store_true",
        help="Sort with lower values first",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    frame = load_runs(args.parent_dir, include_run_path=False)
    if args.runs is not None:
        frame = build_run_report(frame, stat_names=[args.stat], run_names=args.runs)
    else:
        frame = build_run_report(frame, stat_names=[args.stat])

    ranked = sort_runs_by_stat(frame, args.stat, ascending=args.asc).head(args.top_n)
    print(ranked.to_csv(index=False), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

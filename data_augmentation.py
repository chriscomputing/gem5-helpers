# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from gem5_helpers import load_runs, render_run_report_markdown, render_run_report_csv, build_run_report


def _parse_comma_separated_list(raw_value: str, *, option_name: str) -> list[str]:
    values = [item.strip() for item in raw_value.split(",")]
    if not values or any(not value for value in values):
        raise argparse.ArgumentTypeError(f"{option_name} must be a comma-separated list of non-empty names")
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a run report with additional calculations as CSV or Markdown")
    parser.add_argument("parent_dir", type=Path, help="Directory containing gem5 run subdirectories", )

    parser.add_argument("--runs", type=lambda value: _parse_comma_separated_list(value, option_name="--runs"),
        help="Comma-separated run names to include in the table", )

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--csv", action="store_true", help="Render the table as CSV output (default)", )
    output_group.add_argument("--md", action="store_true", help="Render the table as a Markdown table", )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    frame = load_runs(args.parent_dir, include_run_path=False)

    keep_stats: list[str] = ["board.processor.cores.core.numCycles",
                             "board.processor.cores.core.commitStats0.committedInstType::FloatMult",
                             "board.processor.cores.core.commitStats0.committedInstType::FloatMisc",
                             "board.processor.cores.core.commitStats0.committedInstType::IntAlu"]
    frame = build_run_report(frame, keep_stats)

    # IPC_Int = IntAlu / numCycles
    frame['IPC_Int'] = (
            frame['board.processor.cores.core.commitStats0.committedInstType::IntAlu'] /
            frame['board.processor.cores.core.numCycles']
    )

    # IPC_Float = (FloatMult + FloatMisc) / numCycles
    frame['IPC_Float'] = (
            (frame['board.processor.cores.core.commitStats0.committedInstType::FloatMult'] +
             frame['board.processor.cores.core.commitStats0.committedInstType::FloatMisc']) /
            frame['board.processor.cores.core.numCycles']
    )

    # Optional: Shorten names for easier math
    mapping = {
        "board.processor.cores.core.numCycles": "numCycles",
        "board.processor.cores.core.commitStats0.committedInstType::IntAlu": "IntAlu",
        "board.processor.cores.core.commitStats0.committedInstType::FloatMult": "FloatMult",
        "board.processor.cores.core.commitStats0.committedInstType::FloatMisc": "FloatMisc",
    }
    frame = frame.rename(columns=mapping)

    print(frame.to_csv(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

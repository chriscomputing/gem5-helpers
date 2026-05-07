# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from gem5_helpers.runs import load_runs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load gem5 run directories into a pandas dataframe"
    )
    parser.add_argument(
        "parent_dir",
        type=Path,
        help="Directory containing gem5 run subdirectories",
    )
    parser.add_argument(
        "--dump-index",
        type=int,
        default=0,
        help="Zero-based stats dump index to load from each run",
    )
    parser.add_argument(
        "--no-run-path",
        action="store_true",
        help="Omit the run_path column from the output dataframe",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    frame = load_runs(
        args.parent_dir,
        dump_index=args.dump_index,
        include_run_path=not args.no_run_path,
    )
    # print(frame.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

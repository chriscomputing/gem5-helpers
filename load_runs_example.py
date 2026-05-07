# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

from gem5_helpers import load_runs, select_runs


def main() -> int:
    frame = load_runs("examples", include_run_path=False)

    print("All runs:")
    print(frame.to_string(index=False))
    print()

    selected = select_runs(
        frame,
        run_names=["default_op2_loop0"],
        stat_names=["simSeconds", "simTicks"],
    )
    print("Selected run:")
    print(selected.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

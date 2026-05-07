# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

from dataclasses import dataclass
from json import load as json_load
from pathlib import Path
from typing import Any

from .stats import Gem5StatsError, load_stats_file


class Gem5RunError(ValueError):
    """Raised when a gem5 run directory cannot be loaded."""


@dataclass(slots=True)
class Gem5Run:
    """A parsed gem5 run directory."""

    run_name: str
    run_path: Path
    dump_index: int
    stats_dump_count: int
    config: dict[str, Any]
    stats: dict[str, float]

    def to_record(self, include_run_path: bool = True) -> dict[str, Any]:
        """Convert the run into a flat record suitable for a pandas dataframe."""
        record: dict[str, Any] = {
            "run_name": self.run_name,
            "dump_index": self.dump_index,
        }
        if include_run_path:
            record["run_path"] = str(self.run_path)
        record.update(self.stats)
        return record


def _validate_run_dir(run_dir: Path) -> tuple[Path, Path]:
    if not run_dir.exists():
        raise Gem5RunError(f"Run directory does not exist: {run_dir}")
    if not run_dir.is_dir():
        raise Gem5RunError(f"Run path is not a directory: {run_dir}")

    config_path = run_dir / "config.json"
    stats_path = run_dir / "stats.txt"
    if not config_path.is_file():
        raise Gem5RunError(f"Missing config.json in {run_dir}")
    if not stats_path.is_file():
        raise Gem5RunError(f"Missing stats.txt in {run_dir}")
    return config_path, stats_path


def load_run(run_dir: str | Path, dump_index: int = 0) -> Gem5Run:
    """Load a single gem5 run directory."""
    run_path = Path(run_dir).expanduser().resolve()
    config_path, stats_path = _validate_run_dir(run_path)

    with config_path.open("r", encoding="utf-8") as handle:
        config = json_load(handle)
    if not isinstance(config, dict):
        raise Gem5RunError(f"Expected config.json to contain an object: {config_path}")

    try:
        stats, dump_count = load_stats_file(stats_path, dump_index=dump_index)
    except Gem5StatsError as exc:
        raise Gem5RunError(f"Failed to parse stats for {run_path}") from exc

    return Gem5Run(
        run_name=run_path.name,
        run_path=run_path,
        dump_index=dump_index,
        stats_dump_count=dump_count,
        config=config,
        stats=stats,
    )


def discover_run_directories(parent_dir: str | Path) -> list[Path]:
    """Discover valid run directories one level below a parent directory."""
    parent_path = Path(parent_dir).expanduser().resolve()
    if not parent_path.exists():
        raise Gem5RunError(f"Parent directory does not exist: {parent_path}")
    if not parent_path.is_dir():
        raise Gem5RunError(f"Parent path is not a directory: {parent_path}")

    candidates: list[Path] = []
    for child in sorted(parent_path.iterdir(), key=lambda path: path.name):
        if not child.is_dir():
            continue
        if (child / "config.json").is_file() and (child / "stats.txt").is_file():
            candidates.append(child)
    return candidates


def load_runs(
    parent_dir: str | Path,
    dump_index: int = 0,
    include_run_path: bool = True,
):
    """Load all valid run directories beneath a parent directory into a dataframe."""
    run_dirs = discover_run_directories(parent_dir)
    if not run_dirs:
        raise Gem5RunError(f"No valid gem5 run directories found beneath {parent_dir}")

    runs = [load_run(run_dir, dump_index=dump_index) for run_dir in run_dirs]
    records = [run.to_record(include_run_path=include_run_path) for run in runs]

    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise Gem5RunError(
            "pandas is required to assemble the batch dataframe"
        ) from exc

    stat_columns: list[str] = []
    seen = {"run_name", "dump_index"}
    if include_run_path:
        seen.add("run_path")
    for run in runs:
        for stat_name in run.stats:
            if stat_name not in seen:
                seen.add(stat_name)
                stat_columns.append(stat_name)

    columns = ["run_name", "dump_index"]
    if include_run_path:
        columns.append("run_path")
    columns.extend(stat_columns)

    return pd.DataFrame.from_records(records, columns=columns)

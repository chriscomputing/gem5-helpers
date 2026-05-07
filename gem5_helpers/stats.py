from __future__ import annotations

from dataclasses import dataclass
from math import nan
from pathlib import Path
from typing import Iterable

BEGIN_STATS_MARKER = "---------- Begin Simulation Statistics ----------"
END_STATS_MARKER = "---------- End Simulation Statistics   ----------"


class Gem5StatsError(ValueError):
    """Raised when gem5 stats text cannot be parsed."""


@dataclass(slots=True)
class StatsDump:
    """A single stats dump extracted from a stats.txt file."""

    lines: list[str]


def split_stats_dumps(text: str) -> list[StatsDump]:
    """Split a stats.txt payload into individual simulation-statistics dumps."""
    dumps: list[StatsDump] = []
    collecting = False
    current: list[str] = []

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if line == BEGIN_STATS_MARKER:
            if collecting:
                raise Gem5StatsError(
                    f"Nested stats begin marker at line {line_number}"
                )
            collecting = True
            current = []
            continue

        if line == END_STATS_MARKER:
            if not collecting:
                raise Gem5StatsError(
                    f"Unexpected stats end marker at line {line_number}"
                )
            dumps.append(StatsDump(lines=current))
            collecting = False
            current = []
            continue

        if collecting:
            current.append(raw_line)

    if collecting:
        raise Gem5StatsError("stats.txt ended before the final end marker")

    return dumps


def normalize_stat_value(raw_value: str) -> float:
    """Normalize a gem5 stat value into a float."""
    value = raw_value.strip()
    if not value:
        raise Gem5StatsError("Encountered an empty stat value")
    if value.lower() == "nan":
        return nan
    try:
        return float(value)
    except ValueError as exc:
        raise Gem5StatsError(f"Could not parse stat value {raw_value!r}") from exc


def parse_stats_dump(lines: Iterable[str]) -> dict[str, float]:
    """Parse one stats dump into a mapping of stat name -> numeric value."""
    stats: dict[str, float] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].rstrip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            raise Gem5StatsError(
                f"Malformed stats line {line_number}: expected at least two columns"
            )
        stat_name = parts[0]
        stat_value = parts[1]
        stats[stat_name] = normalize_stat_value(stat_value)
    return stats


def load_stats_file(path: Path, dump_index: int = 0) -> tuple[dict[str, float], int]:
    """Load and parse a selected stats dump from a stats.txt file."""
    if dump_index < 0:
        raise Gem5StatsError("dump_index must be greater than or equal to zero")

    text = path.read_text()
    dumps = split_stats_dumps(text)
    if not dumps:
        raise Gem5StatsError(f"No stats dumps found in {path}")
    if dump_index >= len(dumps):
        raise Gem5StatsError(
            f"Requested dump_index {dump_index} but only {len(dumps)} dumps exist in {path}"
        )

    selected_dump = dumps[dump_index]
    return parse_stats_dump(selected_dump.lines), len(dumps)


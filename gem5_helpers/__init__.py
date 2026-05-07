"""Public library API for gem5 output analysis."""

from .runs import Gem5Run, load_run, load_runs
from .stats import (
    BEGIN_STATS_MARKER,
    END_STATS_MARKER,
    Gem5StatsError,
    normalize_stat_value,
    parse_stats_dump,
    split_stats_dumps,
)

__all__ = [
    "BEGIN_STATS_MARKER",
    "END_STATS_MARKER",
    "Gem5Run",
    "Gem5StatsError",
    "load_run",
    "load_runs",
    "normalize_stat_value",
    "parse_stats_dump",
    "split_stats_dumps",
]


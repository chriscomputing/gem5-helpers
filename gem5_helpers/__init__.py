# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

"""Public library API for gem5 output analysis."""

from .analysis import (
    Gem5AnalysisError,
    max_run_by_stat,
    mean_stat,
    min_run_by_stat,
    sort_runs_by_stat,
)
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
    "Gem5AnalysisError",
    "Gem5Run",
    "Gem5StatsError",
    "load_run",
    "load_runs",
    "max_run_by_stat",
    "mean_stat",
    "min_run_by_stat",
    "normalize_stat_value",
    "parse_stats_dump",
    "sort_runs_by_stat",
    "split_stats_dumps",
]

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

from math import isnan
from numbers import Real
from typing import Any


class Gem5AnalysisError(ValueError):
    """Raised when dataframe-based gem5 analysis cannot be performed."""


def _is_nan(value: Any) -> bool:
    return isinstance(value, float) and isnan(value)


def _get_column(frame: Any, stat_name: str):
    if stat_name not in frame.columns:
        raise Gem5AnalysisError(f"Unknown stat column: {stat_name}")

    return frame[stat_name]


def _get_valid_numeric_values(column, stat_name: str) -> list[tuple[int, Real]]:
    valid_values: list[tuple[int, Real]] = []
    for index, value in column.items():
        if _is_nan(value):
            continue
        if not isinstance(value, Real):
            raise Gem5AnalysisError(f"Stat column must be numeric: {stat_name}")
        valid_values.append((index, value))

    if not valid_values:
        raise Gem5AnalysisError(
            f"Stat column has no non-NaN values to analyze: {stat_name}"
        )

    return valid_values


def mean_stat(frame: Any, stat_name: str) -> float:
    """Return the mean value for a numeric stat column across runs."""
    column = _get_column(frame, stat_name)
    valid_values = _get_valid_numeric_values(column, stat_name)
    total = sum(value for _, value in valid_values)
    return float(total / len(valid_values))


def min_run_by_stat(frame: Any, stat_name: str):
    """Return the first run row with the minimum value for a stat column."""
    column = _get_column(frame, stat_name)
    valid_values = _get_valid_numeric_values(column, stat_name)
    min_index = min(valid_values, key=lambda item: item[1])[0]
    return frame.loc[min_index]


def max_run_by_stat(frame: Any, stat_name: str):
    """Return the first run row with the maximum value for a stat column."""
    column = _get_column(frame, stat_name)
    valid_values = _get_valid_numeric_values(column, stat_name)
    max_index = max(valid_values, key=lambda item: item[1])[0]
    return frame.loc[max_index]


def sort_runs_by_stat(frame: Any, stat_name: str, ascending: bool = True):
    """Return runs sorted by a numeric stat column."""
    column = _get_column(frame, stat_name)
    _get_valid_numeric_values(column, stat_name)
    return frame.sort_values(by=stat_name, ascending=ascending, na_position="last")

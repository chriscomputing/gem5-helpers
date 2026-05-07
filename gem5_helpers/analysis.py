# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

from collections.abc import Sequence
import csv
from io import StringIO
from math import isnan
from numbers import Real
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

METADATA_COLUMNS = ("run_name", "dump_index", "run_path")


class Gem5AnalysisError(ValueError):
    """Raised when pandas-based gem5 analysis cannot be performed."""


def _is_nan(value: Any) -> bool:
    return isinstance(value, float) and isnan(value)


def _normalize_requested_names(
    names: Sequence[str],
    *,
    kind: str,
    allow_empty: bool = False,
) -> list[str]:
    if isinstance(names, str):
        raise Gem5AnalysisError(f"{kind} selection must be a sequence of names")
    if not names:
        if allow_empty:
            return []
        raise Gem5AnalysisError(f"At least one {kind} must be selected")

    requested_names = list(names)
    if not all(isinstance(name, str) for name in requested_names):
        raise Gem5AnalysisError(f"{kind} values must be strings")

    duplicates = sorted({name for name in requested_names if requested_names.count(name) > 1})
    if duplicates:
        raise Gem5AnalysisError(
            f"Duplicate {kind}s are not allowed: {', '.join(duplicates)}"
        )
    return requested_names


def _get_column(frame: pd.DataFrame, column_name: str):
    if column_name not in frame.columns:
        raise Gem5AnalysisError(f"Unknown stat column: {column_name}")
    return frame[column_name]


def _get_run_names(frame: pd.DataFrame) -> list[str]:
    if "run_name" not in frame.columns:
        raise Gem5AnalysisError("Analysis frame must include a run_name column")

    run_names = frame["run_name"].tolist()
    if not all(isinstance(run_name, str) for run_name in run_names):
        raise Gem5AnalysisError("run_name values must be strings")

    duplicates = sorted({name for name in run_names if run_names.count(name) > 1})
    if duplicates:
        raise Gem5AnalysisError(
            f"Duplicate run_names are not allowed in the frame: {', '.join(duplicates)}"
        )
    return run_names


def _get_stat_names(frame: pd.DataFrame) -> list[str]:
    _get_run_names(frame)
    return [column_name for column_name in frame.columns if column_name not in METADATA_COLUMNS]


def _validate_stat_names(
    frame: pd.DataFrame,
    stat_names: Sequence[str] | None,
) -> list[str]:
    if stat_names is None:
        return _get_stat_names(frame)

    requested_stat_names = _normalize_requested_names(stat_names, kind="stat_name")
    for stat_name in requested_stat_names:
        _get_column(frame, stat_name)
    return requested_stat_names


def _select_rows(frame: pd.DataFrame, run_names: Sequence[str] | None):
    available_run_names = _get_run_names(frame)
    if run_names is None:
        return frame

    requested_run_names = _normalize_requested_names(run_names, kind="run_name")
    missing_run_names = [
        run_name for run_name in requested_run_names if run_name not in available_run_names
    ]
    if missing_run_names:
        raise Gem5AnalysisError(f"Unknown run name: {', '.join(missing_run_names)}")

    return frame.set_index("run_name", drop=False).loc[requested_run_names].reset_index(
        drop=True
    )


def _format_report_value(value: Any) -> str:
    if value is None or _is_nan(value):
        return "NaN"
    return str(value)


def _iter_formatted_report_rows(report) -> tuple[list[str], list[list[str]]]:
    columns = list(report.columns)
    rows = [
        [_format_report_value(record.get(column_name)) for column_name in columns]
        for record in report.to_dict(orient="records")
    ]
    return columns, rows


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


def build_run_report(
    frame: pd.DataFrame,
    stat_names: Sequence[str],
    run_names: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return a narrow dataframe containing run_name and selected stat columns."""
    requested_stat_names = _validate_stat_names(frame, stat_names)
    return select_runs(frame, run_names=run_names, stat_names=requested_stat_names)[
        ["run_name", *requested_stat_names]
    ]


def list_run_names(frame: pd.DataFrame) -> list[str]:
    """Return run names in the current dataframe row order."""
    return _get_run_names(frame)


def list_stat_names(frame: pd.DataFrame) -> list[str]:
    """Return stat-column names in dataframe column order."""
    return _get_stat_names(frame)


def select_runs(
    frame: pd.DataFrame,
    run_names: Sequence[str] | None = None,
    stat_names: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return a filtered dataframe for selected runs and stat columns."""
    requested_stat_names = _validate_stat_names(frame, stat_names)
    selected_frame = _select_rows(frame, run_names)
    columns = [column_name for column_name in METADATA_COLUMNS if column_name in frame.columns]
    return selected_frame[[*columns, *requested_stat_names]]


def render_run_report_markdown(
    frame: pd.DataFrame,
    stat_names: Sequence[str],
    run_names: Sequence[str] | None = None,
) -> str:
    """Render a selected run report as a Markdown table."""
    columns, rows = _iter_formatted_report_rows(
        build_run_report(frame, stat_names, run_names=run_names)
    )
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def render_run_report_csv(
    frame: pd.DataFrame,
    stat_names: Sequence[str],
    run_names: Sequence[str] | None = None,
) -> str:
    """Render a selected run report as CSV text."""
    columns, rows = _iter_formatted_report_rows(
        build_run_report(frame, stat_names, run_names=run_names)
    )
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    writer.writerows(rows)
    return output.getvalue()


def mean_stat(frame: pd.DataFrame, stat_name: str) -> float:
    """Return the mean value for a numeric stat column across runs."""
    column = _get_column(frame, stat_name)
    valid_values = _get_valid_numeric_values(column, stat_name)
    total = sum(value for _, value in valid_values)
    return float(total / len(valid_values))


def min_run_by_stat(frame: pd.DataFrame, stat_name: str):
    """Return the first run row with the minimum value for a stat column."""
    column = _get_column(frame, stat_name)
    valid_values = _get_valid_numeric_values(column, stat_name)
    min_index = min(valid_values, key=lambda item: item[1])[0]
    return frame.loc[min_index]


def max_run_by_stat(frame: pd.DataFrame, stat_name: str):
    """Return the first run row with the maximum value for a stat column."""
    column = _get_column(frame, stat_name)
    valid_values = _get_valid_numeric_values(column, stat_name)
    max_index = max(valid_values, key=lambda item: item[1])[0]
    return frame.loc[max_index]


def sort_runs_by_stat(frame: pd.DataFrame, stat_name: str, ascending: bool = True):
    """Return runs sorted by a numeric stat column."""
    column = _get_column(frame, stat_name)
    _get_valid_numeric_values(column, stat_name)
    return frame.sort_values(by=stat_name, ascending=ascending, na_position="last")

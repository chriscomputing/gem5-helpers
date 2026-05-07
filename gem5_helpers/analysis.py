# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

import csv
from io import StringIO
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


def _require_run_name_column(frame: Any) -> None:
    if "run_name" not in frame.columns:
        raise Gem5AnalysisError("Report frame must include a run_name column")


def _normalize_requested_names(
    names: list[str] | tuple[str, ...],
    *,
    kind: str,
) -> list[str]:
    if not names:
        raise Gem5AnalysisError(f"At least one {kind} must be selected")

    seen: set[str] = set()
    duplicates: list[str] = []
    for name in names:
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)

    if duplicates:
        raise Gem5AnalysisError(
            f"Duplicate {kind}s are not allowed: {', '.join(duplicates)}"
        )

    return list(names)


def _get_row_value(row: Any, column_name: str) -> Any:
    if isinstance(row, dict):
        return row.get(column_name)

    try:
        return row[column_name]
    except (KeyError, TypeError, IndexError):
        getter = getattr(row, "get", None)
        if getter is None:
            return None
        return getter(column_name)


def _build_row_index_by_run_name(frame: Any) -> dict[str, int]:
    _require_run_name_column(frame)

    run_name_column = frame["run_name"]
    row_index_by_run_name: dict[str, int] = {}
    duplicates: list[str] = []
    for index, run_name in run_name_column.items():
        if not isinstance(run_name, str):
            raise Gem5AnalysisError("run_name values must be strings")
        if run_name in row_index_by_run_name and run_name not in duplicates:
            duplicates.append(run_name)
        row_index_by_run_name[run_name] = index

    if duplicates:
        raise Gem5AnalysisError(
            f"Duplicate run_names are not allowed in the frame: {', '.join(duplicates)}"
        )

    return row_index_by_run_name


def _get_report_row_indexes(frame: Any, run_names: list[str] | tuple[str, ...] | None):
    row_index_by_run_name = _build_row_index_by_run_name(frame)
    if run_names is None:
        return list(row_index_by_run_name.values())

    requested_run_names = _normalize_requested_names(run_names, kind="run_name")
    missing_run_names = [
        run_name for run_name in requested_run_names if run_name not in row_index_by_run_name
    ]
    if missing_run_names:
        raise Gem5AnalysisError(
            f"Unknown run name: {', '.join(missing_run_names)}"
        )

    return [row_index_by_run_name[run_name] for run_name in requested_run_names]


def _format_report_value(value: Any) -> str:
    if value is None or _is_nan(value):
        return "NaN"
    return str(value)


def _iter_frame_rows(frame: Any):
    _require_run_name_column(frame)
    for row_index, _ in frame["run_name"].items():
        yield frame.loc[row_index]


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
    frame: Any,
    stat_names: list[str] | tuple[str, ...],
    run_names: list[str] | tuple[str, ...] | None = None,
):
    """Return a narrow dataframe containing run_name and selected stat columns."""
    requested_stat_names = _normalize_requested_names(stat_names, kind="stat_name")
    _require_run_name_column(frame)
    for stat_name in requested_stat_names:
        _get_column(frame, stat_name)

    row_indexes = _get_report_row_indexes(frame, run_names)
    columns = ["run_name", *requested_stat_names]
    records: list[dict[str, Any]] = []
    for row_index in row_indexes:
        row = frame.loc[row_index]
        record = {"run_name": _get_row_value(row, "run_name")}
        for stat_name in requested_stat_names:
            record[stat_name] = _get_row_value(row, stat_name)
        records.append(record)

    return frame.__class__.from_records(records, columns=columns)


def render_run_report_markdown(
    frame: Any,
    stat_names: list[str] | tuple[str, ...],
    run_names: list[str] | tuple[str, ...] | None = None,
) -> str:
    """Render a selected run report as a Markdown table."""
    report = build_run_report(frame, stat_names, run_names=run_names)
    columns = list(report.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in _iter_frame_rows(report):
        lines.append(
            "| "
            + " | ".join(
                _format_report_value(_get_row_value(row, column_name))
                for column_name in columns
            )
            + " |"
        )
    return "\n".join(lines)


def render_run_report_csv(
    frame: Any,
    stat_names: list[str] | tuple[str, ...],
    run_names: list[str] | tuple[str, ...] | None = None,
) -> str:
    """Render a selected run report as CSV text."""
    report = build_run_report(frame, stat_names, run_names=run_names)
    output = StringIO()
    writer = csv.writer(output)
    columns = list(report.columns)
    writer.writerow(columns)
    for row in _iter_frame_rows(report):
        writer.writerow(
            [_format_report_value(_get_row_value(row, column_name)) for column_name in columns]
        )
    return output.getvalue()


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

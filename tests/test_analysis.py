# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

from math import nan
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from gem5_helpers.analysis import (
    Gem5AnalysisError,
    max_run_by_stat,
    mean_stat,
    min_run_by_stat,
    sort_runs_by_stat,
)


class FakeSeries:
    def __init__(self, values: list[object], index: list[int]) -> None:
        self._values = values
        self._index = index

    def items(self):
        return zip(self._index, self._values)


class FakeLoc:
    def __init__(self, frame: FakeDataFrame) -> None:
        self._frame = frame

    def __getitem__(self, index: int) -> dict[str, object]:
        return dict(self._frame._records[index])


class FakeDataFrame:
    def __init__(self, records: list[dict[str, object]], columns: list[str]) -> None:
        self._records = records
        self.columns = columns
        self.loc = FakeLoc(self)

    @classmethod
    def from_records(
        cls, records: list[dict[str, object]], columns: list[str]
    ) -> FakeDataFrame:
        return cls(records=[dict(record) for record in records], columns=columns)

    def __getitem__(self, key: str) -> FakeSeries:
        return FakeSeries(
            values=[record.get(key) for record in self._records],
            index=list(range(len(self._records))),
        )

    def __setitem__(self, key: str, value: object) -> None:
        if key not in self.columns:
            self.columns.append(key)
        for record in self._records:
            record[key] = value

    def sort_values(
        self, by: str, ascending: bool = True, na_position: str = "last"
    ) -> FakeDataFrame:
        if na_position != "last":
            raise AssertionError("FakeDataFrame only supports na_position='last'")

        def is_nan_value(value: object) -> bool:
            return isinstance(value, float) and value != value

        def key_fn(item: tuple[int, dict[str, object]]):
            value = item[1].get(by)
            return (is_nan_value(value), value)

        sorted_items = sorted(
            enumerate(self._records), key=key_fn, reverse=not ascending
        )

        if not ascending:
            non_nan = [
                record for _, record in sorted_items if not is_nan_value(record.get(by))
            ]
            nan_records = [
                record for _, record in sorted_items if is_nan_value(record.get(by))
            ]
            sorted_records = non_nan + nan_records
        else:
            sorted_records = [record for _, record in sorted_items]

        return FakeDataFrame(
            records=[dict(record) for record in sorted_records],
            columns=list(self.columns),
        )


def fake_pandas_module() -> types.ModuleType:
    module = types.ModuleType("pandas")
    module.DataFrame = FakeDataFrame
    return module


class AnalysisTests(unittest.TestCase):
    def load_frame(self) -> FakeDataFrame:
        from gem5_helpers.runs import load_runs

        with patch.dict(sys.modules, {"pandas": fake_pandas_module()}):
            return load_runs(Path("examples"))

    def test_mean_stat_returns_mean_for_numeric_column(self) -> None:
        frame = self.load_frame()
        self.assertAlmostEqual(mean_stat(frame, "simSeconds"), 0.0016505)

    def test_min_run_by_stat_returns_run_with_lowest_value(self) -> None:
        frame = self.load_frame()
        run = min_run_by_stat(frame, "simSeconds")
        self.assertEqual(run["run_name"], "default_op2_loop0")
        self.assertAlmostEqual(run["simSeconds"], 0.000451)

    def test_max_run_by_stat_returns_run_with_highest_value(self) -> None:
        frame = self.load_frame()
        run = max_run_by_stat(frame, "simSeconds")
        self.assertEqual(run["run_name"], "config1_loop1")
        self.assertAlmostEqual(run["simSeconds"], 0.00285)

    def test_sort_runs_by_stat_sorts_ascending(self) -> None:
        frame = self.load_frame()
        sorted_frame = sort_runs_by_stat(frame, "simSeconds")
        self.assertEqual(
            [run["run_name"] for run in sorted_frame._records],
            ["default_op2_loop0", "config1_loop1"],
        )

    def test_sort_runs_by_stat_sorts_descending(self) -> None:
        frame = self.load_frame()
        sorted_frame = sort_runs_by_stat(frame, "simSeconds", ascending=False)
        self.assertEqual(
            [run["run_name"] for run in sorted_frame._records],
            ["config1_loop1", "default_op2_loop0"],
        )

    def test_analysis_rejects_unknown_stat_column(self) -> None:
        frame = self.load_frame()
        with self.assertRaisesRegex(Gem5AnalysisError, "Unknown stat column"):
            mean_stat(frame, "does_not_exist")

    def test_analysis_rejects_non_numeric_column(self) -> None:
        frame = self.load_frame()
        with self.assertRaisesRegex(Gem5AnalysisError, "must be numeric"):
            mean_stat(frame, "run_name")

    def test_mean_stat_skips_nan_values(self) -> None:
        frame = self.load_frame()
        frame._records[0]["simSeconds"] = nan
        self.assertAlmostEqual(mean_stat(frame, "simSeconds"), 0.000451)

    def test_min_run_by_stat_ignores_nan_values(self) -> None:
        frame = self.load_frame()
        frame._records[1]["simSeconds"] = nan
        run = min_run_by_stat(frame, "simSeconds")
        self.assertEqual(run["run_name"], "config1_loop1")

    def test_sort_runs_by_stat_places_nan_values_last(self) -> None:
        frame = self.load_frame()
        frame._records[0]["simSeconds"] = nan
        sorted_frame = sort_runs_by_stat(frame, "simSeconds")
        self.assertEqual(
            [run["run_name"] for run in sorted_frame._records],
            ["default_op2_loop0", "config1_loop1"],
        )

    def test_analysis_rejects_all_nan_column(self) -> None:
        frame = self.load_frame()
        frame["simSeconds"] = nan

        with self.assertRaisesRegex(Gem5AnalysisError, "no non-NaN values"):
            mean_stat(frame, "simSeconds")

        with self.assertRaisesRegex(Gem5AnalysisError, "no non-NaN values"):
            min_run_by_stat(frame, "simSeconds")

        with self.assertRaisesRegex(Gem5AnalysisError, "no non-NaN values"):
            max_run_by_stat(frame, "simSeconds")


if __name__ == "__main__":
    unittest.main()

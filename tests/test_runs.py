# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from gem5_helpers.runs import Gem5RunError, load_run


class FakeDataFrame:
    def __init__(self, records: list[dict], columns: list[str]) -> None:
        self._records = records
        self.columns = columns

    @classmethod
    def from_records(cls, records: list[dict], columns: list[str]):
        return cls(records=records, columns=columns)

    def __getitem__(self, key: str):
        return [record.get(key) for record in self._records]

    def __len__(self) -> int:
        return len(self._records)


def fake_pandas_module() -> types.ModuleType:
    module = types.ModuleType("pandas")
    module.DataFrame = FakeDataFrame
    return module


class RunLoadingTests(unittest.TestCase):
    def test_load_single_run_defaults_to_first_dump(self) -> None:
        run = load_run(Path("examples/config1_loop1"))
        self.assertEqual(run.run_name, "config1_loop1")
        self.assertEqual(run.dump_index, 0)
        self.assertAlmostEqual(run.stats["simSeconds"], 0.00285)
        self.assertIn("type", run.config)

    def test_load_single_run_selects_second_dump(self) -> None:
        run = load_run(Path("examples/config1_loop1"), dump_index=1)
        self.assertAlmostEqual(run.stats["simSeconds"], 0.002869)

    def test_load_run_rejects_missing_directory(self) -> None:
        with self.assertRaises(Gem5RunError):
            load_run(Path("examples/does_not_exist"))

    def test_load_runs_creates_wide_dataframe_with_run_name(self) -> None:
        from gem5_helpers.runs import load_runs

        with patch.dict(sys.modules, {"pandas": fake_pandas_module()}):
            frame = load_runs(Path("examples"))
        self.assertEqual(list(frame["run_name"]), ["config1_loop1", "default_op2_loop0"])
        self.assertIn("run_path", frame.columns)
        self.assertIn("simSeconds", frame.columns)
        self.assertEqual(len(frame), 2)

    def test_load_runs_can_omit_run_path(self) -> None:
        from gem5_helpers.runs import load_runs

        with patch.dict(sys.modules, {"pandas": fake_pandas_module()}):
            frame = load_runs(Path("examples"), include_run_path=False)
        self.assertNotIn("run_path", frame.columns)
        self.assertIn("run_name", frame.columns)


if __name__ == "__main__":
    unittest.main()

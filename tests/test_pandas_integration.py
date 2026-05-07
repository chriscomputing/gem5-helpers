# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

from pathlib import Path
import unittest

try:
    import pandas as pd
except ImportError:  # pragma: no cover - environment dependent
    pd = None

from gem5_helpers import (
    build_run_report,
    list_run_names,
    list_stat_names,
    load_runs,
    render_run_report_csv,
    render_run_report_markdown,
    select_runs,
    sort_runs_by_stat,
)


@unittest.skipIf(pd is None, "pandas is not installed")
class PandasIntegrationTests(unittest.TestCase):
    def test_load_runs_returns_documented_dataframe_schema(self) -> None:
        frame = load_runs(Path("examples"))
        self.assertIsInstance(frame, pd.DataFrame)
        self.assertEqual(list(frame.columns[:3]), ["run_name", "dump_index", "run_path"])
        self.assertIn("simSeconds", frame.columns)
        self.assertIn("simTicks", frame.columns)
        self.assertEqual(frame["run_name"].tolist(), ["config1_loop1", "default_op2_loop0"])

    def test_custom_analysis_script_flow_works_with_real_pandas(self) -> None:
        frame = load_runs(Path("examples"), include_run_path=False)

        self.assertEqual(list_run_names(frame), ["config1_loop1", "default_op2_loop0"])
        self.assertIn("simSeconds", list_stat_names(frame))

        selected = select_runs(
            frame,
            run_names=["default_op2_loop0", "config1_loop1"],
            stat_names=["simSeconds", "simTicks"],
        )
        self.assertEqual(
            list(selected.columns),
            ["run_name", "dump_index", "simSeconds", "simTicks"],
        )
        self.assertEqual(
            selected["run_name"].tolist(),
            ["default_op2_loop0", "config1_loop1"],
        )

        sorted_frame = sort_runs_by_stat(frame, "simSeconds")
        self.assertEqual(
            sorted_frame["run_name"].tolist(),
            ["default_op2_loop0", "config1_loop1"],
        )

        report = build_run_report(frame, ["simSeconds", "simTicks"])
        self.assertEqual(
            list(report.columns),
            ["run_name", "simSeconds", "simTicks"],
        )

        markdown_table = render_run_report_markdown(
            frame,
            stat_names=["simSeconds", "simTicks"],
            run_names=["default_op2_loop0", "config1_loop1"],
        )
        csv_text = render_run_report_csv(
            frame,
            stat_names=["simSeconds", "simTicks"],
            run_names=["default_op2_loop0", "config1_loop1"],
        )

        self.assertIn("| run_name | simSeconds | simTicks |", markdown_table)
        self.assertIn("default_op2_loop0,0.000451,450521000.0", csv_text)


if __name__ == "__main__":
    unittest.main()

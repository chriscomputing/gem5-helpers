# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

from math import nan
import unittest

from gem5_helpers.analysis import (
    Gem5AnalysisError,
    build_run_report,
    list_run_names,
    list_stat_names,
    max_run_by_stat,
    mean_stat,
    min_run_by_stat,
    render_run_report_csv,
    render_run_report_markdown,
    select_runs,
    sort_runs_by_stat,
)
from tests._fake_pandas import FakeDataFrame, load_fake_frame


class AnalysisTests(unittest.TestCase):
    def load_frame(self, include_run_path: bool = True) -> FakeDataFrame:
        return load_fake_frame(include_run_path=include_run_path)

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

    def test_build_run_report_returns_selected_columns_in_requested_order(self) -> None:
        frame = self.load_frame()
        report = build_run_report(
            frame,
            ["simSeconds", "simTicks"],
            run_names=["default_op2_loop0", "config1_loop1"],
        )
        self.assertEqual(report.columns, ["run_name", "simSeconds", "simTicks"])

    def test_build_run_report_uses_requested_run_order(self) -> None:
        frame = self.load_frame()
        report = build_run_report(
            frame,
            ["simSeconds"],
            run_names=["default_op2_loop0", "config1_loop1"],
        )
        self.assertEqual(
            [run["run_name"] for run in report._records],
            ["default_op2_loop0", "config1_loop1"],
        )

    def test_build_run_report_preserves_frame_order_when_runs_not_selected(self) -> None:
        frame = self.load_frame()
        report = build_run_report(frame, ["simSeconds"])
        self.assertEqual(
            [run["run_name"] for run in report._records],
            ["config1_loop1", "default_op2_loop0"],
        )

    def test_list_run_names_returns_frame_order(self) -> None:
        frame = self.load_frame()
        self.assertEqual(
            list_run_names(frame),
            ["config1_loop1", "default_op2_loop0"],
        )

    def test_list_stat_names_omits_metadata_columns(self) -> None:
        frame = self.load_frame()
        stat_names = list_stat_names(frame)
        self.assertIn("simSeconds", stat_names)
        self.assertIn("simTicks", stat_names)
        self.assertNotIn("run_name", stat_names)
        self.assertNotIn("dump_index", stat_names)
        self.assertNotIn("run_path", stat_names)

    def test_select_runs_filters_runs_and_stats(self) -> None:
        frame = self.load_frame()
        selected = select_runs(
            frame,
            run_names=["default_op2_loop0"],
            stat_names=["simTicks", "simSeconds"],
        )
        self.assertEqual(
            selected.columns,
            ["run_name", "dump_index", "run_path", "simTicks", "simSeconds"],
        )
        self.assertEqual(len(selected._records), 1)
        self.assertEqual(selected._records[0]["run_name"], "default_op2_loop0")
        self.assertEqual(selected._records[0]["simTicks"], 450521000.0)
        self.assertEqual(selected._records[0]["simSeconds"], 0.000451)

    def test_select_runs_preserves_frame_order_by_default(self) -> None:
        frame = self.load_frame()
        selected = select_runs(frame, stat_names=["simSeconds"])
        self.assertEqual(
            [run["run_name"] for run in selected._records],
            ["config1_loop1", "default_op2_loop0"],
        )

    def test_select_runs_defaults_to_all_stats(self) -> None:
        frame = self.load_frame(include_run_path=False)
        selected = select_runs(frame, run_names=["config1_loop1"])
        self.assertEqual(selected.columns[:2], ["run_name", "dump_index"])
        self.assertIn("simSeconds", selected.columns)
        self.assertIn("simTicks", selected.columns)

    def test_render_run_report_markdown_renders_table(self) -> None:
        frame = self.load_frame()
        report = render_run_report_markdown(
            frame,
            ["simSeconds", "simTicks"],
            run_names=["default_op2_loop0", "config1_loop1"],
        )
        self.assertEqual(
            report,
            "\n".join(
                [
                    "| run_name | simSeconds | simTicks |",
                    "| --- | --- | --- |",
                    "| default_op2_loop0 | 0.000451 | 450521000.0 |",
                    "| config1_loop1 | 0.00285 | 2850201000.0 |",
                ]
            ),
        )

    def test_render_run_report_csv_renders_rows(self) -> None:
        frame = self.load_frame()
        report = render_run_report_csv(
            frame,
            ["simSeconds", "simTicks"],
            run_names=["default_op2_loop0", "config1_loop1"],
        )
        self.assertEqual(
            report,
            (
                "run_name,simSeconds,simTicks\r\n"
                "default_op2_loop0,0.000451,450521000.0\r\n"
                "config1_loop1,0.00285,2850201000.0\r\n"
            ),
        )

    def test_render_run_report_outputs_nan_for_missing_or_nan_values(self) -> None:
        frame = self.load_frame()
        frame._records[0]["simSeconds"] = nan
        frame._records[1].pop("simTicks")
        markdown_report = render_run_report_markdown(frame, ["simSeconds", "simTicks"])
        csv_report = render_run_report_csv(frame, ["simSeconds", "simTicks"])
        self.assertIn("| config1_loop1 | NaN | 2850201000.0 |", markdown_report)
        self.assertIn("| default_op2_loop0 | 0.000451 | NaN |", markdown_report)
        self.assertIn("config1_loop1,NaN,2850201000.0", csv_report)
        self.assertIn("default_op2_loop0,0.000451,NaN", csv_report)

    def test_report_helpers_work_without_run_path_column(self) -> None:
        frame = self.load_frame(include_run_path=False)
        report = build_run_report(frame, ["simSeconds"])
        self.assertEqual(report.columns, ["run_name", "simSeconds"])
        self.assertEqual(
            render_run_report_markdown(frame, ["simSeconds"]),
            "\n".join(
                [
                    "| run_name | simSeconds |",
                    "| --- | --- |",
                    "| config1_loop1 | 0.00285 |",
                    "| default_op2_loop0 | 0.000451 |",
                ]
            ),
        )

    def test_build_run_report_rejects_unknown_stat_name(self) -> None:
        frame = self.load_frame()
        for helper_name, reporter in (
            ("build_run_report", lambda: build_run_report(frame, ["does_not_exist"])),
            ("select_runs", lambda: select_runs(frame, stat_names=["does_not_exist"])),
        ):
            with self.subTest(helper=helper_name):
                with self.assertRaisesRegex(Gem5AnalysisError, "Unknown stat column"):
                    reporter()

    def test_build_run_report_rejects_unknown_run_name(self) -> None:
        frame = self.load_frame()
        for helper_name, reporter in (
            (
                "build_run_report",
                lambda: build_run_report(
                    frame, ["simSeconds"], run_names=["does_not_exist"]
                ),
            ),
            (
                "select_runs",
                lambda: select_runs(
                    frame,
                    run_names=["does_not_exist"],
                    stat_names=["simSeconds"],
                ),
            ),
        ):
            with self.subTest(helper=helper_name):
                with self.assertRaisesRegex(Gem5AnalysisError, "Unknown run name"):
                    reporter()

    def test_build_run_report_rejects_empty_stat_names(self) -> None:
        frame = self.load_frame()
        with self.assertRaisesRegex(Gem5AnalysisError, "At least one stat_name"):
            build_run_report(frame, [])

    def test_build_run_report_rejects_duplicate_stat_names(self) -> None:
        frame = self.load_frame()
        for helper_name, reporter in (
            (
                "build_run_report",
                lambda: build_run_report(frame, ["simSeconds", "simSeconds"]),
            ),
            (
                "select_runs",
                lambda: select_runs(frame, stat_names=["simSeconds", "simSeconds"]),
            ),
        ):
            with self.subTest(helper=helper_name):
                with self.assertRaisesRegex(Gem5AnalysisError, "Duplicate stat_names"):
                    reporter()

    def test_build_run_report_rejects_duplicate_run_names(self) -> None:
        frame = self.load_frame()
        for helper_name, reporter in (
            (
                "build_run_report",
                lambda: build_run_report(
                    frame,
                    ["simSeconds"],
                    run_names=["config1_loop1", "config1_loop1"],
                ),
            ),
            (
                "select_runs",
                lambda: select_runs(
                    frame,
                    run_names=["config1_loop1", "config1_loop1"],
                    stat_names=["simSeconds"],
                ),
            ),
        ):
            with self.subTest(helper=helper_name):
                with self.assertRaisesRegex(Gem5AnalysisError, "Duplicate run_names"):
                    reporter()

    def test_build_run_report_delegates_selection_behavior(self) -> None:
        frame = self.load_frame()
        self.assertEqual(
            build_run_report(
                frame,
                ["simTicks", "simSeconds"],
                run_names=["default_op2_loop0"],
            )._records,
            [
                {
                    "run_name": "default_op2_loop0",
                    "simTicks": 450521000.0,
                    "simSeconds": 0.000451,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()

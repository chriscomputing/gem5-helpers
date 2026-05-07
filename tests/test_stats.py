from __future__ import annotations

from pathlib import Path
import unittest

from gem5_helpers.stats import (
    BEGIN_STATS_MARKER,
    END_STATS_MARKER,
    Gem5StatsError,
    normalize_stat_value,
    parse_stats_dump,
    split_stats_dumps,
)


class StatsParsingTests(unittest.TestCase):
    def test_split_stats_dumps_finds_two_dumps_in_sample_file(self) -> None:
        text = Path("examples/config1_loop1/stats.txt").read_text()
        dumps = split_stats_dumps(text)
        self.assertEqual(len(dumps), 2)

    def test_parse_stats_dump_uses_only_first_two_columns(self) -> None:
        dump = [
            "my.stat.name\t42\tignored\tcolumns\t# comment",
            "another.stat    nan    more stuff    # comment",
        ]
        stats = parse_stats_dump(dump)
        self.assertEqual(stats["my.stat.name"], 42.0)
        self.assertTrue(stats["another.stat"] != stats["another.stat"])

    def test_normalize_stat_value_handles_nan_and_floats(self) -> None:
        self.assertEqual(normalize_stat_value("1.25"), 1.25)
        self.assertTrue(normalize_stat_value("nan") != normalize_stat_value("nan"))

    def test_split_stats_dumps_errors_on_unclosed_dump(self) -> None:
        text = "\n".join(
            [
                BEGIN_STATS_MARKER,
                "stat_name 1",
            ]
        )
        with self.assertRaises(Gem5StatsError):
            split_stats_dumps(text)

    def test_parse_stats_dump_errors_on_malformed_line(self) -> None:
        with self.assertRaises(Gem5StatsError):
            parse_stats_dump(["only_one_column"])

    def test_split_stats_dumps_errors_on_unexpected_end_marker(self) -> None:
        with self.assertRaises(Gem5StatsError):
            split_stats_dumps(END_STATS_MARKER)


if __name__ == "__main__":
    unittest.main()


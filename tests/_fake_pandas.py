# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 chriscomputing

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys
import types
from typing import Any
from unittest.mock import patch


class FakeSeries:
    def __init__(self, values: list[object], index: list[object]) -> None:
        self._values = values
        self._index = index

    def __iter__(self):
        return iter(self._values)

    def items(self):
        return zip(self._index, self._values)

    def tolist(self) -> list[object]:
        return list(self._values)


class FakeLoc:
    def __init__(self, frame: FakeDataFrame) -> None:
        self._frame = frame

    def __getitem__(self, key):
        if isinstance(key, tuple):
            row_key, column_key = key
            return self._select_rows(row_key)[column_key]

        selected = self._select_rows(key)
        if isinstance(key, list):
            return selected
        return dict(selected._records[0])

    def _select_rows(self, key) -> FakeDataFrame:
        if isinstance(key, list):
            selected_records: list[dict[str, object]] = []
            selected_index: list[object] = []
            for row_label in key:
                position = self._frame._index.index(row_label)
                selected_records.append(dict(self._frame._records[position]))
                selected_index.append(self._frame._index[position])
            return FakeDataFrame(
                records=selected_records,
                columns=list(self._frame.columns),
                index=selected_index,
            )

        position = self._frame._index.index(key)
        return FakeDataFrame(
            records=[dict(self._frame._records[position])],
            columns=list(self._frame.columns),
            index=[self._frame._index[position]],
        )


class FakeDataFrame:
    def __init__(
        self,
        records: list[dict[str, object]],
        columns: list[str],
        index: list[object] | None = None,
    ) -> None:
        self._records = [dict(record) for record in records]
        self.columns = columns
        self._index = list(range(len(self._records))) if index is None else list(index)
        self.loc = FakeLoc(self)

    @classmethod
    def from_records(
        cls, records: list[dict[str, object]], columns: list[str]
    ) -> FakeDataFrame:
        return cls(records=records, columns=columns)

    def __getitem__(self, key):
        if isinstance(key, str):
            return FakeSeries(
                values=[record.get(key) for record in self._records],
                index=list(self._index),
            )

        columns = list(key)
        return FakeDataFrame(
            records=[
                {column_name: record.get(column_name) for column_name in columns}
                for record in self._records
            ],
            columns=columns,
            index=list(self._index),
        )

    def __setitem__(self, key: str, value: object) -> None:
        if key not in self.columns:
            self.columns.append(key)
        for record in self._records:
            record[key] = value

    def __len__(self) -> int:
        return len(self._records)

    def set_index(self, column_name: str, drop: bool = False) -> FakeDataFrame:
        columns = [column for column in self.columns if column != column_name] if drop else list(self.columns)
        return FakeDataFrame(
            records=[
                {
                    column: record.get(column)
                    for column in columns
                }
                for record in self._records
            ],
            columns=columns,
            index=[record.get(column_name) for record in self._records],
        )

    def reset_index(self, drop: bool = False) -> FakeDataFrame:
        return FakeDataFrame(records=self._records, columns=list(self.columns))

    def sort_values(
        self, by: str, ascending: bool = True, na_position: str = "last"
    ) -> FakeDataFrame:
        if na_position != "last":
            raise AssertionError("FakeDataFrame only supports na_position='last'")

        def is_nan_value(value: object) -> bool:
            return isinstance(value, float) and value != value

        def key_fn(item: tuple[object, dict[str, object]]):
            value = item[1].get(by)
            return (is_nan_value(value), value)

        sorted_items = sorted(
            zip(self._index, self._records), key=key_fn, reverse=not ascending
        )

        if not ascending:
            non_nan = [item for item in sorted_items if not is_nan_value(item[1].get(by))]
            nan_items = [item for item in sorted_items if is_nan_value(item[1].get(by))]
            sorted_items = non_nan + nan_items

        return FakeDataFrame(
            records=[dict(record) for _, record in sorted_items],
            columns=list(self.columns),
            index=[index for index, _ in sorted_items],
        )

    def to_dict(self, orient: str) -> list[dict[str, object]]:
        if orient != "records":
            raise AssertionError("FakeDataFrame only supports orient='records'")
        return [dict(record) for record in self._records]


def fake_pandas_module() -> types.ModuleType:
    module = types.ModuleType("pandas")
    module.DataFrame = FakeDataFrame
    return module


@contextmanager
def patched_fake_pandas():
    with patch.dict(sys.modules, {"pandas": fake_pandas_module()}):
        yield


def load_fake_frame(include_run_path: bool = True) -> FakeDataFrame:
    from gem5_helpers.runs import load_runs

    with patched_fake_pandas():
        return load_runs(Path("examples"), include_run_path=include_run_path)

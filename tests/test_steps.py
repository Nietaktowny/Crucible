import pytest
from datetime import date, datetime, time, timedelta
from pathlib import Path

from pydantic import ValidationError
import polars as pl
import pandas as pd

from crucible.models import StepConfig, StepExecutionContext
from crucible.steps import (
    SelectColumnsStep,
    ChangeColumnTypeStep,
    ConcatStep,
    CreateColumnStep,
    DateAddStep,
    DateDiffStep,
    DatePeriodFilterStep,
    DateRangeFilterStep,
    DropNullsStep,
    ExtractDateTimePartStep,
    ExtractDateTimeStep,
    FillDownStep,
    FillNullsStep,
    FilterRowsStep,
    GroupByStep,
    JoinStep,
    LimitRowsStep,
    ParseDateTimeStep,
    PivotStep,
    ReadCsvStep,
    ReadExcelStep,
    ReadFolderCsvStep,
    ReadFolderExcelStep,
    RegexExtractStep,
    RemoveDuplicatesStep,
    RenameColumnsStep,
    ReorderColumnsStep,
    ReplaceValuesStep,
    SortRowsStep,
    SplitColumnStep,
    UnpivotStep,
    WriteCsvStep,
    WriteExcelStep
)

def test_change_column_type_casts_single_column_to_int32():
    df = pl.DataFrame({"value": ["1", "2", "3"]}).lazy()

    step = ChangeColumnTypeStep(
        StepConfig(
            key="change_column_type",
            parameters={"column_types": {"value": "int32"}},
        )
    )

    result = step.execute(df).collect()

    assert result.schema["value"] == pl.Int32
    assert result["value"].to_list() == [1, 2, 3]


def test_change_column_type_casts_multiple_columns():
    df = pl.DataFrame(
        {
            "id": ["1", "2"],
            "price": ["10.5", "20.25"],
            "created_at": ["2026-06-09", "2026-06-10"],
        }
    ).lazy()

    step = ChangeColumnTypeStep(
        StepConfig(
            key="change_column_type",
            parameters={
                "column_types": {
                    "id": "int64",
                    "price": "float64",
                    "created_at": "date",
                }
            },
        )
    )

    result = step.execute(df).collect()

    assert result.schema["id"] == pl.Int64
    assert result.schema["price"] == pl.Float64
    assert result.schema["created_at"] == pl.Date

    assert result["id"].to_list() == [1, 2]
    assert result["price"].to_list() == [10.5, 20.25]

@pytest.mark.parametrize(
    ("type_name", "input_value", "expected_dtype"),
    [
        ("string", 123, pl.String),
        ("text", 123, pl.String),
        ("int8", "1", pl.Int8),
        ("int16", "1", pl.Int16),
        ("int32", "1", pl.Int32),
        ("int64", "1", pl.Int64),
        ("uint8", "1", pl.UInt8),
        ("uint16", "1", pl.UInt16),
        ("uint32", "1", pl.UInt32),
        ("uint64", "1", pl.UInt64),
        ("float32", "1.5", pl.Float32),
        ("float64", "1.5", pl.Float64),
        ("boolean", 1, pl.Boolean),
        ("date", date(2026, 6, 9), pl.Date),
        ("datetime", datetime(2026, 6, 9, 12, 30), pl.Datetime),
        ("time", time(12, 30), pl.Time),
    ],
)
def test_change_column_type_supports_declared_type_names(
    type_name,
    input_value,
    expected_dtype,
):
    df = pl.DataFrame({"value": [input_value]}).lazy()

    step = ChangeColumnTypeStep(
        StepConfig(
            key="change_column_type",
            parameters={"column_types": {"value": type_name}},
        )
    )

    result = step.execute(df).collect()

    assert result.schema["value"] == expected_dtype

def test_change_column_type_preserves_unlisted_columns():
    df = pl.DataFrame(
        {
            "id": ["1", "2"],
            "name": ["A", "B"],
        }
    ).lazy()

    step = ChangeColumnTypeStep(
        StepConfig(
            key="change_column_type",
            parameters={"column_types": {"id": "int64"}},
        )
    )

    result = step.execute(df).collect()

    assert result.schema["id"] == pl.Int64
    assert result.schema["name"] == pl.String
    assert result["name"].to_list() == ["A", "B"]


def test_change_column_type_returns_lazyframe():
    df = pl.DataFrame({"value": ["1"]}).lazy()

    step = ChangeColumnTypeStep(
        StepConfig(
            key="change_column_type",
            parameters={"column_types": {"value": "int64"}},
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_change_column_type_rejects_unknown_type_name():
    with pytest.raises(ValidationError):
        ChangeColumnTypeStep(
            StepConfig(
                key="change_column_type",
                parameters={"column_types": {"value": "decimal"}},
            )
        )


def test_change_column_type_raises_when_column_does_not_exist():
    df = pl.DataFrame({"value": ["1"]}).lazy()

    step = ChangeColumnTypeStep(
        StepConfig(
            key="change_column_type",
            parameters={"column_types": {"missing": "int64"}},
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_change_column_type_raises_when_value_cannot_be_cast():
    df = pl.DataFrame({"value": ["not-a-number"]}).lazy()

    step = ChangeColumnTypeStep(
        StepConfig(
            key="change_column_type",
            parameters={"column_types": {"value": "int64"}},
        )
    )

    with pytest.raises(pl.exceptions.InvalidOperationError):
        step.execute(df).collect()

def test_concat_vertical_appends_rows_from_extra_inputs():
    data = pl.DataFrame({"id": [1], "name": ["A"]}).lazy()
    extra = pl.DataFrame({"id": [2], "name": ["B"]}).lazy()

    context = StepExecutionContext(extra_inputs={"second": extra})

    step = ConcatStep(
        StepConfig(
            key="concat",
            parameters={"how": "vertical"},
        )
    )

    result = step.execute(data, context).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", "B"],
    }


def test_concat_uses_vertical_by_default():
    data = pl.DataFrame({"id": [1]}).lazy()
    extra = pl.DataFrame({"id": [2]}).lazy()

    context = StepExecutionContext(extra_inputs={"second": extra})

    step = ConcatStep(
        StepConfig(
            key="concat",
            parameters={},
        )
    )

    result = step.execute(data, context).collect()

    assert result["id"].to_list() == [1, 2]


def test_concat_diagonal_allows_different_schemas():
    data = pl.DataFrame({"id": [1], "name": ["A"]}).lazy()
    extra = pl.DataFrame({"id": [2], "score": [100]}).lazy()

    context = StepExecutionContext(extra_inputs={"second": extra})

    step = ConcatStep(
        StepConfig(
            key="concat",
            parameters={"how": "diagonal"},
        )
    )

    result = step.execute(data, context).collect()

    assert result.columns == ["id", "name", "score"]
    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", None],
        "score": [None, 100],
    }


def test_concat_horizontal_appends_columns():
    data = pl.DataFrame({"id": [1, 2]}).lazy()
    extra = pl.DataFrame({"name": ["A", "B"]}).lazy()

    context = StepExecutionContext(extra_inputs={"second": extra})

    step = ConcatStep(
        StepConfig(
            key="concat",
            parameters={"how": "horizontal"},
        )
    )

    result = step.execute(data, context).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", "B"],
    }


def test_concat_clears_context_extra_inputs_after_execution():
    data = pl.DataFrame({"id": [1]}).lazy()
    extra = pl.DataFrame({"id": [2]}).lazy()

    context = StepExecutionContext(extra_inputs={"second": extra})

    step = ConcatStep(
        StepConfig(
            key="concat",
            parameters={"how": "vertical"},
        )
    )

    step.execute(data, context)

    assert context.extra_inputs == {}


def test_concat_returns_lazyframe():
    data = pl.DataFrame({"id": [1]}).lazy()
    extra = pl.DataFrame({"id": [2]}).lazy()

    context = StepExecutionContext(extra_inputs={"second": extra})

    step = ConcatStep(
        StepConfig(
            key="concat",
            parameters={"how": "vertical"},
        )
    )

    result = step.execute(data, context)

    assert isinstance(result, pl.LazyFrame)


def test_concat_rejects_invalid_how_value():
    with pytest.raises(ValidationError):
        ConcatStep(
            StepConfig(
                key="concat",
                parameters={"how": "outer"},
            )
        )


def test_concat_vertical_raises_for_different_schemas():
    data = pl.DataFrame({"id": [1]}).lazy()
    extra = pl.DataFrame({"name": ["A"]}).lazy()

    context = StepExecutionContext(extra_inputs={"second": extra})

    step = ConcatStep(
        StepConfig(
            key="concat",
            parameters={"how": "vertical"},
        )
    )

    with pytest.raises(pl.exceptions.InvalidOperationError):
        step.execute(data, context).collect()


def test_concat_fails_without_context():
    data = pl.DataFrame({"id": [1]}).lazy()

    step = ConcatStep(
        StepConfig(
            key="concat",
            parameters={"how": "vertical"},
        )
    )

    with pytest.raises(AttributeError):
        step.execute(data, None)
        
def test_create_column_creates_literal_column():
    df = pl.DataFrame({"id": [1, 2]}).lazy()

    step = CreateColumnStep(
        StepConfig(
            key="create_column",
            parameters={
                "name": "source",
                "expr": {"value": "manual"},
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "source": ["manual", "manual"],
    }


def test_create_column_creates_column_from_existing_column_expression():
    df = pl.DataFrame({"value": [10, 20]}).lazy()

    step = CreateColumnStep(
        StepConfig(
            key="create_column",
            parameters={
                "name": "copied_value",
                "expr": {"column": "value"},
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "value": [10, 20],
        "copied_value": [10, 20],
    }


def test_create_column_creates_column_from_add_operation():
    df = pl.DataFrame({"a": [10, 20], "b": [1, 2]}).lazy()

    step = CreateColumnStep(
        StepConfig(
            key="create_column",
            parameters={
                "name": "sum",
                "expr": {
                    "op": "add",
                    "args": [
                        {"column": "a"},
                        {"column": "b"},
                    ],
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "a": [10, 20],
        "b": [1, 2],
        "sum": [11, 22],
    }


def test_create_column_can_overwrite_existing_column():
    df = pl.DataFrame({"value": [10, 20]}).lazy()

    step = CreateColumnStep(
        StepConfig(
            key="create_column",
            parameters={
                "name": "value",
                "expr": {"value": 999},
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "value": [999, 999],
    }


def test_create_column_returns_lazyframe():
    df = pl.DataFrame({"id": [1]}).lazy()

    step = CreateColumnStep(
        StepConfig(
            key="create_column",
            parameters={
                "name": "new_column",
                "expr": {"value": 1},
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_create_column_rejects_missing_name():
    with pytest.raises(ValidationError):
        CreateColumnStep(
            StepConfig(
                key="create_column",
                parameters={
                    "expr": {"value": 1},
                },
            )
        )


def test_create_column_rejects_missing_expression():
    with pytest.raises(ValidationError):
        CreateColumnStep(
            StepConfig(
                key="create_column",
                parameters={
                    "name": "new_column",
                },
            )
        )


def test_create_column_rejects_unknown_operation():
    with pytest.raises(ValidationError):
        CreateColumnStep(
            StepConfig(
                key="create_column",
                parameters={
                    "name": "bad_column",
                    "expr": {
                        "op": "unknown_operation",
                        "args": [{"column": "a"}],
                    },
                },
            )
        )


def test_create_column_raises_when_referenced_column_does_not_exist():
    df = pl.DataFrame({"id": [1]}).lazy()

    step = CreateColumnStep(
        StepConfig(
            key="create_column",
            parameters={
                "name": "missing_copy",
                "expr": {"column": "missing"},
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_date_add_adds_days_to_date_column():
    df = pl.DataFrame(
        {
            "date": [date(2026, 6, 1)],
        }
    ).lazy()

    step = DateAddStep(
        StepConfig(
            key="date_add",
            parameters={
                "column": "date",
                "value": 5,
                "unit": "days",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["date"].to_list() == [date(2026, 6, 6)]


def test_date_add_subtracts_days_using_negative_value():
    df = pl.DataFrame(
        {
            "date": [date(2026, 6, 10)],
        }
    ).lazy()

    step = DateAddStep(
        StepConfig(
            key="date_add",
            parameters={
                "column": "date",
                "value": -5,
                "unit": "days",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["date"].to_list() == [date(2026, 6, 5)]


def test_date_add_writes_to_output_column():
    df = pl.DataFrame(
        {
            "date": [date(2026, 6, 1)],
        }
    ).lazy()

    step = DateAddStep(
        StepConfig(
            key="date_add",
            parameters={
                "column": "date",
                "value": 1,
                "unit": "days",
                "output_column": "date_plus_one",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.columns == ["date", "date_plus_one"]
    assert result["date"].to_list() == [date(2026, 6, 1)]
    assert result["date_plus_one"].to_list() == [date(2026, 6, 2)]


@pytest.mark.parametrize(
    ("unit", "value", "expected"),
    [
        ("hours", 1, datetime(2026, 6, 1, 13, 0, 0)),
        ("minutes", 30, datetime(2026, 6, 1, 12, 30, 0)),
        ("seconds", 45, datetime(2026, 6, 1, 12, 0, 45)),
        ("milliseconds", 500, datetime(2026, 6, 1, 12, 0, 0, 500000)),
    ],
)
def test_date_add_supports_all_datetime_units(unit, value, expected):
    df = pl.DataFrame(
        {
            "dt": [datetime(2026, 6, 1, 12, 0, 0)],
        }
    ).lazy()

    step = DateAddStep(
        StepConfig(
            key="date_add",
            parameters={
                "column": "dt",
                "value": value,
                "unit": unit,
            },
        )
    )

    result = step.execute(df).collect()

    assert result["dt"].to_list() == [expected]


def test_date_add_overwrites_source_column_when_output_column_not_specified():
    df = pl.DataFrame(
        {
            "date": [date(2026, 6, 1)],
        }
    ).lazy()

    step = DateAddStep(
        StepConfig(
            key="date_add",
            parameters={
                "column": "date",
                "value": 1,
                "unit": "days",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.columns == ["date"]
    assert result["date"].to_list() == [date(2026, 6, 2)]


def test_date_add_returns_lazyframe():
    df = pl.DataFrame(
        {
            "date": [date(2026, 6, 1)],
        }
    ).lazy()

    step = DateAddStep(
        StepConfig(
            key="date_add",
            parameters={
                "column": "date",
                "value": 1,
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_date_add_rejects_invalid_unit():
    with pytest.raises(ValidationError):
        DateAddStep(
            StepConfig(
                key="date_add",
                parameters={
                    "column": "date",
                    "value": 1,
                    "unit": "weeks",
                },
            )
        )


def test_date_add_raises_for_missing_column():
    df = pl.DataFrame(
        {
            "date": [date(2026, 6, 1)],
        }
    ).lazy()

    step = DateAddStep(
        StepConfig(
            key="date_add",
            parameters={
                "column": "missing",
                "value": 1,
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_date_diff_between_two_datetime_columns_in_days():
    df = pl.DataFrame(
        {
            "start": [datetime(2026, 6, 1)],
            "end": [datetime(2026, 6, 6)],
        }
    ).lazy()

    step = DateDiffStep(
        StepConfig(
            key="date_diff",
            parameters={
                "start_column": "start",
                "end_column": "end",
                "unit": "days",
                "output_column": "diff_days",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["diff_days"].to_list() == [5]


@pytest.mark.parametrize(
    ("unit", "expected"),
    [
        ("days", 1),
        ("hours", 27),
        ("minutes", 1620),
        ("seconds", 97200),
        ("milliseconds", 97200000),
    ],
)
def test_date_diff_supports_all_units(unit, expected):
    df = pl.DataFrame(
        {
            "start": [datetime(2026, 6, 1, 10, 0, 0)],
            "end": [datetime(2026, 6, 2, 13, 0, 0)],
        }
    ).lazy()

    step = DateDiffStep(
        StepConfig(
            key="date_diff",
            parameters={
                "start_column": "start",
                "end_column": "end",
                "unit": unit,
                "output_column": "diff",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["diff"].to_list() == [expected]


def test_date_diff_between_start_value_and_end_column():
    df = pl.DataFrame(
        {
            "end": [datetime(2026, 6, 10)],
        }
    ).lazy()

    step = DateDiffStep(
        StepConfig(
            key="date_diff",
            parameters={
                "start_value": "2026-06-01",
                "end_column": "end",
                "unit": "days",
                "output_column": "diff_days",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["diff_days"].to_list() == [9]


def test_date_diff_between_start_column_and_end_value():
    df = pl.DataFrame(
        {
            "start": [datetime(2026, 6, 1)],
        }
    ).lazy()

    step = DateDiffStep(
        StepConfig(
            key="date_diff",
            parameters={
                "start_column": "start",
                "end_value": "2026-06-10",
                "unit": "days",
                "output_column": "diff_days",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["diff_days"].to_list() == [9]


def test_date_diff_between_two_literal_values():
    df = pl.DataFrame({"id": [1]}).lazy()

    step = DateDiffStep(
        StepConfig(
            key="date_diff",
            parameters={
                "start_value": "2026-06-01",
                "end_value": "2026-06-10",
                "unit": "days",
                "output_column": "diff_days",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "diff_days": [9],
    }


def test_date_diff_can_return_negative_difference():
    df = pl.DataFrame(
        {
            "start": [datetime(2026, 6, 10)],
            "end": [datetime(2026, 6, 1)],
        }
    ).lazy()

    step = DateDiffStep(
        StepConfig(
            key="date_diff",
            parameters={
                "start_column": "start",
                "end_column": "end",
                "unit": "days",
                "output_column": "diff_days",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["diff_days"].to_list() == [-9]


def test_date_diff_returns_lazyframe():
    df = pl.DataFrame(
        {
            "start": [datetime(2026, 6, 1)],
            "end": [datetime(2026, 6, 2)],
        }
    ).lazy()

    step = DateDiffStep(
        StepConfig(
            key="date_diff",
            parameters={
                "start_column": "start",
                "end_column": "end",
                "output_column": "diff_days",
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_date_diff_rejects_missing_start():
    with pytest.raises(ValidationError):
        DateDiffStep(
            StepConfig(
                key="date_diff",
                parameters={
                    "end_column": "end",
                    "output_column": "diff_days",
                },
            )
        )


def test_date_diff_rejects_missing_end():
    with pytest.raises(ValidationError):
        DateDiffStep(
            StepConfig(
                key="date_diff",
                parameters={
                    "start_column": "start",
                    "output_column": "diff_days",
                },
            )
        )


def test_date_diff_rejects_start_column_and_start_value_together():
    with pytest.raises(ValidationError):
        DateDiffStep(
            StepConfig(
                key="date_diff",
                parameters={
                    "start_column": "start",
                    "start_value": "2026-06-01",
                    "end_column": "end",
                    "output_column": "diff_days",
                },
            )
        )


def test_date_diff_rejects_end_column_and_end_value_together():
    with pytest.raises(ValidationError):
        DateDiffStep(
            StepConfig(
                key="date_diff",
                parameters={
                    "start_column": "start",
                    "end_column": "end",
                    "end_value": "2026-06-01",
                    "output_column": "diff_days",
                },
            )
        )


def test_date_diff_rejects_invalid_unit():
    with pytest.raises(ValidationError):
        DateDiffStep(
            StepConfig(
                key="date_diff",
                parameters={
                    "start_column": "start",
                    "end_column": "end",
                    "unit": "weeks",
                    "output_column": "diff",
                },
            )
        )


def test_date_diff_raises_for_missing_start_column():
    df = pl.DataFrame(
        {
            "end": [datetime(2026, 6, 1)],
        }
    ).lazy()

    step = DateDiffStep(
        StepConfig(
            key="date_diff",
            parameters={
                "start_column": "missing",
                "end_column": "end",
                "output_column": "diff_days",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
    
def test_date_period_filter_current_year():
    today = date.today()

    df = pl.DataFrame(
        {
            "date": [
                today,
                date(today.year, 1, 1),
                date(today.year - 1, today.month, today.day),
            ],
            "value": [1, 2, 3],
        }
    ).lazy()

    step = DatePeriodFilterStep(
        StepConfig(
            key="date_period_filter",
            parameters={
                "column": "date",
                "period": "current_year",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == [1, 2]


def test_date_period_filter_current_month():
    today = date.today()

    previous_month = (
        date(today.year - 1, 12, 1)
        if today.month == 1
        else date(today.year, today.month - 1, 1)
    )

    df = pl.DataFrame(
        {
            "date": [
                today,
                date(today.year, today.month, 1),
                previous_month,
                date(today.year - 1, today.month, today.day),
            ],
            "value": [1, 2, 3, 4],
        }
    ).lazy()

    step = DatePeriodFilterStep(
        StepConfig(
            key="date_period_filter",
            parameters={
                "column": "date",
                "period": "current_month",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == [1, 2]


def test_date_period_filter_current_day():
    today = date.today()
    yesterday = today - timedelta(days=1)

    df = pl.DataFrame(
        {
            "date": [
                today,
                yesterday,
                date(today.year - 1, today.month, today.day),
            ],
            "value": [1, 2, 3],
        }
    ).lazy()

    step = DatePeriodFilterStep(
        StepConfig(
            key="date_period_filter",
            parameters={
                "column": "date",
                "period": "current_day",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "date": [today],
        "value": [1],
    }


def test_date_period_filter_returns_lazyframe():
    today = date.today()

    df = pl.DataFrame({"date": [today]}).lazy()

    step = DatePeriodFilterStep(
        StepConfig(
            key="date_period_filter",
            parameters={
                "column": "date",
                "period": "current_day",
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_date_period_filter_rejects_invalid_period():
    with pytest.raises(ValidationError):
        DatePeriodFilterStep(
            StepConfig(
                key="date_period_filter",
                parameters={
                    "column": "date",
                    "period": "current_week",
                },
            )
        )


def test_date_period_filter_rejects_missing_column_parameter():
    with pytest.raises(ValidationError):
        DatePeriodFilterStep(
            StepConfig(
                key="date_period_filter",
                parameters={
                    "period": "current_day",
                },
            )
        )


def test_date_period_filter_rejects_missing_period_parameter():
    with pytest.raises(ValidationError):
        DatePeriodFilterStep(
            StepConfig(
                key="date_period_filter",
                parameters={
                    "column": "date",
                },
            )
        )


def test_date_period_filter_raises_for_missing_dataframe_column():
    today = date.today()

    df = pl.DataFrame({"date": [today]}).lazy()

    step = DatePeriodFilterStep(
        StepConfig(
            key="date_period_filter",
            parameters={
                "column": "missing",
                "period": "current_day",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_date_period_filter_raises_for_non_temporal_column():
    df = pl.DataFrame({"date": ["2026-06-09"]}).lazy()

    step = DatePeriodFilterStep(
        StepConfig(
            key="date_period_filter",
            parameters={
                "column": "date",
                "period": "current_day",
            },
        )
    )

    with pytest.raises(pl.exceptions.InvalidOperationError):
        step.execute(df).collect()
        
def test_date_range_filter_filters_dates_inclusive_by_default():
    df = pl.DataFrame(
        {
            "date": [
                date(2026, 6, 1),
                date(2026, 6, 5),
                date(2026, 6, 10),
            ],
            "value": [1, 2, 3],
        }
    ).lazy()

    step = DateRangeFilterStep(
        StepConfig(
            key="date_range_filter",
            parameters={
                "column": "date",
                "start": "2026-06-01",
                "end": "2026-06-10",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == [1, 2, 3]


def test_date_range_filter_closed_none_excludes_boundaries():
    df = pl.DataFrame(
        {
            "date": [
                date(2026, 6, 1),
                date(2026, 6, 5),
                date(2026, 6, 10),
            ],
            "value": [1, 2, 3],
        }
    ).lazy()

    step = DateRangeFilterStep(
        StepConfig(
            key="date_range_filter",
            parameters={
                "column": "date",
                "start": "2026-06-01",
                "end": "2026-06-10",
                "closed": "none",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == [2]


def test_date_range_filter_closed_left():
    df = pl.DataFrame(
        {
            "date": [
                date(2026, 6, 1),
                date(2026, 6, 5),
                date(2026, 6, 10),
            ],
            "value": [1, 2, 3],
        }
    ).lazy()

    step = DateRangeFilterStep(
        StepConfig(
            key="date_range_filter",
            parameters={
                "column": "date",
                "start": "2026-06-01",
                "end": "2026-06-10",
                "closed": "left",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == [1, 2]


def test_date_range_filter_closed_right():
    df = pl.DataFrame(
        {
            "date": [
                date(2026, 6, 1),
                date(2026, 6, 5),
                date(2026, 6, 10),
            ],
            "value": [1, 2, 3],
        }
    ).lazy()

    step = DateRangeFilterStep(
        StepConfig(
            key="date_range_filter",
            parameters={
                "column": "date",
                "start": "2026-06-01",
                "end": "2026-06-10",
                "closed": "right",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == [2, 3]


def test_date_range_filter_supports_datetime_values():
    df = pl.DataFrame(
        {
            "dt": [
                datetime(2026, 6, 1, 10, 0),
                datetime(2026, 6, 5, 12, 0),
                datetime(2026, 6, 10, 15, 0),
            ],
            "value": [1, 2, 3],
        }
    ).lazy()

    step = DateRangeFilterStep(
        StepConfig(
            key="date_range_filter",
            parameters={
                "column": "dt",
                "start": "2026-06-01T00:00:00",
                "end": "2026-06-10T23:59:59",
                "value_type": "datetime",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == [1, 2, 3]


def test_date_range_filter_returns_empty_when_nothing_matches():
    df = pl.DataFrame(
        {
            "date": [date(2026, 6, 1)],
        }
    ).lazy()

    step = DateRangeFilterStep(
        StepConfig(
            key="date_range_filter",
            parameters={
                "column": "date",
                "start": "2026-07-01",
                "end": "2026-07-31",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.height == 0


def test_date_range_filter_returns_lazyframe():
    df = pl.DataFrame(
        {
            "date": [date(2026, 6, 1)],
        }
    ).lazy()

    step = DateRangeFilterStep(
        StepConfig(
            key="date_range_filter",
            parameters={
                "column": "date",
                "start": "2026-06-01",
                "end": "2026-06-10",
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_date_range_filter_rejects_invalid_value_type():
    with pytest.raises(ValidationError):
        DateRangeFilterStep(
            StepConfig(
                key="date_range_filter",
                parameters={
                    "column": "date",
                    "start": "2026-06-01",
                    "end": "2026-06-10",
                    "value_type": "timestamp",
                },
            )
        )


def test_date_range_filter_rejects_invalid_closed_value():
    with pytest.raises(ValidationError):
        DateRangeFilterStep(
            StepConfig(
                key="date_range_filter",
                parameters={
                    "column": "date",
                    "start": "2026-06-01",
                    "end": "2026-06-10",
                    "closed": "inclusive",
                },
            )
        )


def test_date_range_filter_raises_for_missing_column():
    df = pl.DataFrame(
        {
            "date": [date(2026, 6, 1)],
        }
    ).lazy()

    step = DateRangeFilterStep(
        StepConfig(
            key="date_range_filter",
            parameters={
                "column": "missing",
                "start": "2026-06-01",
                "end": "2026-06-10",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_date_range_filter_raises_for_invalid_date_literal():
    df = pl.DataFrame(
        {
            "date": [date(2026, 6, 1)],
        }
    ).lazy()

    step = DateRangeFilterStep(
        StepConfig(
            key="date_range_filter",
            parameters={
                "column": "date",
                "start": "not-a-date",
                "end": "2026-06-10",
            },
        )
    )

    with pytest.raises(ValueError):
        step.execute(df).collect()


def test_date_range_filter_raises_for_invalid_datetime_literal():
    df = pl.DataFrame(
        {
            "dt": [datetime(2026, 6, 1, 10, 0)],
        }
    ).lazy()

    step = DateRangeFilterStep(
        StepConfig(
            key="date_range_filter",
            parameters={
                "column": "dt",
                "start": "not-a-datetime",
                "end": "2026-06-10T00:00:00",
                "value_type": "datetime",
            },
        )
    )

    with pytest.raises(ValueError):
        step.execute(df).collect()
        
def test_drop_nulls_removes_rows_with_any_nulls_by_default():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["A", None, "C"],
            "value": [10, 20, None],
        }
    ).lazy()

    step = DropNullsStep(
        StepConfig(
            key="drop_nulls",
            parameters={},
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "name": ["A"],
        "value": [10],
    }


def test_drop_nulls_only_checks_specified_column():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["A", None, "C"],
            "value": [10, 20, None],
        }
    ).lazy()

    step = DropNullsStep(
        StepConfig(
            key="drop_nulls",
            parameters={
                "columns": ["name"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1, 3],
        "name": ["A", "C"],
        "value": [10, None],
    }


def test_drop_nulls_multiple_columns_subset():
    df = pl.DataFrame(
        {
            "a": [1, None, 3, None],
            "b": [10, 20, None, None],
        }
    ).lazy()

    step = DropNullsStep(
        StepConfig(
            key="drop_nulls",
            parameters={
                "columns": ["a", "b"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "a": [1],
        "b": [10],
    }


def test_drop_nulls_keeps_rows_when_no_nulls_exist():
    df = pl.DataFrame(
        {
            "id": [1, 2],
            "name": ["A", "B"],
        }
    ).lazy()

    step = DropNullsStep(
        StepConfig(
            key="drop_nulls",
            parameters={},
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", "B"],
    }


def test_drop_nulls_returns_empty_dataframe_when_all_rows_contain_nulls():
    df = pl.DataFrame(
        {
            "a": [None, None],
            "b": [1, None],
        }
    ).lazy()

    step = DropNullsStep(
        StepConfig(
            key="drop_nulls",
            parameters={},
        )
    )

    result = step.execute(df).collect()

    assert result.height == 0


def test_drop_nulls_returns_lazyframe():
    df = pl.DataFrame(
        {
            "id": [1],
        }
    ).lazy()

    step = DropNullsStep(
        StepConfig(
            key="drop_nulls",
            parameters={},
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_drop_nulls_raises_for_missing_column():
    df = pl.DataFrame(
        {
            "id": [1],
        }
    ).lazy()

    step = DropNullsStep(
        StepConfig(
            key="drop_nulls",
            parameters={
                "columns": ["missing"],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_drop_nulls_accepts_explicit_none_columns():
    df = pl.DataFrame(
        {
            "id": [1, 2],
            "value": [10, None],
        }
    ).lazy()

    step = DropNullsStep(
        StepConfig(
            key="drop_nulls",
            parameters={
                "columns": None,
            },
        )
    )

    result = step.execute(df).collect()

    assert result["id"].to_list() == [1]
    
@pytest.mark.parametrize(
    ("part", "expected"),
    [
        ("year", 2026),
        ("month", 6),
        ("day", 9),
        ("week", 24),
        ("weekday", 2),
        ("hour", 13),
        ("minute", 45),
        ("second", 30),
    ],
)
def test_extract_datetime_part_extracts_supported_parts(part, expected):
    df = pl.DataFrame(
        {
            "dt": [datetime(2026, 6, 9, 13, 45, 30)],
        }
    ).lazy()

    step = ExtractDateTimePartStep(
        StepConfig(
            key="extract_datetime_part",
            parameters={
                "column": "dt",
                "part": part,
            },
        )
    )

    result = step.execute(df).collect()

    assert result[f"dt_{part}"].to_list() == [expected]


def test_extract_datetime_part_uses_custom_output_column():
    df = pl.DataFrame(
        {
            "dt": [datetime(2026, 6, 9, 13, 45, 30)],
        }
    ).lazy()

    step = ExtractDateTimePartStep(
        StepConfig(
            key="extract_datetime_part",
            parameters={
                "column": "dt",
                "part": "year",
                "output_column": "rok",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.columns == ["dt", "rok"]
    assert result["rok"].to_list() == [2026]


def test_extract_datetime_part_returns_lazyframe():
    df = pl.DataFrame(
        {
            "dt": [datetime(2026, 6, 9, 13, 45, 30)],
        }
    ).lazy()

    step = ExtractDateTimePartStep(
        StepConfig(
            key="extract_datetime_part",
            parameters={
                "column": "dt",
                "part": "year",
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_extract_datetime_part_rejects_invalid_part():
    with pytest.raises(ValidationError):
        ExtractDateTimePartStep(
            StepConfig(
                key="extract_datetime_part",
                parameters={
                    "column": "dt",
                    "part": "quarter",
                },
            )
        )


def test_extract_datetime_part_raises_for_missing_column():
    df = pl.DataFrame(
        {
            "dt": [datetime(2026, 6, 9, 13, 45, 30)],
        }
    ).lazy()

    step = ExtractDateTimePartStep(
        StepConfig(
            key="extract_datetime_part",
            parameters={
                "column": "missing",
                "part": "year",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_extract_datetime_part_raises_for_non_temporal_column():
    df = pl.DataFrame(
        {
            "dt": ["2026-06-09 13:45:30"],
        }
    ).lazy()

    step = ExtractDateTimePartStep(
        StepConfig(
            key="extract_datetime_part",
            parameters={
                "column": "dt",
                "part": "year",
            },
        )
    )

    with pytest.raises(pl.exceptions.InvalidOperationError):
        step.execute(df).collect()
        
def test_extract_datetime_extracts_date():
    df = pl.DataFrame(
        {
            "dt": [datetime(2026, 6, 9, 13, 45, 30)],
        }
    ).lazy()

    step = ExtractDateTimeStep(
        StepConfig(
            key="extract_date_time",
            parameters={
                "column": "dt",
                "extract": "date",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["dt_date"].to_list() == [date(2026, 6, 9)]


def test_extract_datetime_extracts_time():
    df = pl.DataFrame(
        {
            "dt": [datetime(2026, 6, 9, 13, 45, 30)],
        }
    ).lazy()

    step = ExtractDateTimeStep(
        StepConfig(
            key="extract_date_time",
            parameters={
                "column": "dt",
                "extract": "time",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["dt_time"].to_list() == [time(13, 45, 30)]


def test_extract_datetime_uses_custom_output_column():
    df = pl.DataFrame(
        {
            "dt": [datetime(2026, 6, 9, 13, 45, 30)],
        }
    ).lazy()

    step = ExtractDateTimeStep(
        StepConfig(
            key="extract_date_time",
            parameters={
                "column": "dt",
                "extract": "date",
                "output_column": "measurement_date",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.columns == ["dt", "measurement_date"]
    assert result["measurement_date"].to_list() == [
        date(2026, 6, 9)
    ]


def test_extract_datetime_returns_lazyframe():
    df = pl.DataFrame(
        {
            "dt": [datetime(2026, 6, 9, 13, 45, 30)],
        }
    ).lazy()

    step = ExtractDateTimeStep(
        StepConfig(
            key="extract_date_time",
            parameters={
                "column": "dt",
                "extract": "date",
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_extract_datetime_rejects_invalid_extract_value():
    with pytest.raises(ValidationError):
        ExtractDateTimeStep(
            StepConfig(
                key="extract_date_time",
                parameters={
                    "column": "dt",
                    "extract": "year",
                },
            )
        )


def test_extract_datetime_raises_for_missing_column():
    df = pl.DataFrame(
        {
            "dt": [datetime(2026, 6, 9, 13, 45, 30)],
        }
    ).lazy()

    step = ExtractDateTimeStep(
        StepConfig(
            key="extract_date_time",
            parameters={
                "column": "missing",
                "extract": "date",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_extract_datetime_raises_for_non_temporal_column():
    df = pl.DataFrame(
        {
            "dt": ["2026-06-09 13:45:30"],
        }
    ).lazy()

    step = ExtractDateTimeStep(
        StepConfig(
            key="extract_date_time",
            parameters={
                "column": "dt",
                "extract": "date",
            },
        )
    )

    with pytest.raises(pl.exceptions.ComputeError):
        step.execute(df).collect()
        
def test_fill_down_fills_nulls_with_previous_non_null_value():
    df = pl.DataFrame(
        {
            "value": [1, None, None, 4, None],
        }
    ).lazy()

    step = FillDownStep(
        StepConfig(
            key="fill_down",
            parameters={
                "columns": ["value"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == [1, 1, 1, 4, 4]


def test_fill_down_fills_multiple_columns():
    df = pl.DataFrame(
        {
            "a": [1, None, 3, None],
            "b": ["x", None, None, "y"],
        }
    ).lazy()

    step = FillDownStep(
        StepConfig(
            key="fill_down",
            parameters={
                "columns": ["a", "b"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "a": [1, 1, 3, 3],
        "b": ["x", "x", "x", "y"],
    }


def test_fill_down_preserves_leading_nulls():
    df = pl.DataFrame(
        {
            "value": [None, None, 3, None],
        }
    ).lazy()

    step = FillDownStep(
        StepConfig(
            key="fill_down",
            parameters={
                "columns": ["value"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == [None, None, 3, 3]


def test_fill_down_does_not_modify_unlisted_columns():
    df = pl.DataFrame(
        {
            "a": [1, None],
            "b": [10, None],
        }
    ).lazy()

    step = FillDownStep(
        StepConfig(
            key="fill_down",
            parameters={
                "columns": ["a"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "a": [1, 1],
        "b": [10, None],
    }


def test_fill_down_returns_lazyframe():
    df = pl.DataFrame({"value": [1, None]}).lazy()

    step = FillDownStep(
        StepConfig(
            key="fill_down",
            parameters={
                "columns": ["value"],
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_fill_down_rejects_missing_columns_parameter():
    with pytest.raises(ValidationError):
        FillDownStep(
            StepConfig(
                key="fill_down",
                parameters={},
            )
        )


def test_fill_down_raises_for_missing_dataframe_column():
    df = pl.DataFrame({"value": [1]}).lazy()

    step = FillDownStep(
        StepConfig(
            key="fill_down",
            parameters={
                "columns": ["missing"],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_fill_nulls_replaces_nulls_in_single_column():
    df = pl.DataFrame(
        {
            "value": [1, None, 3],
        }
    ).lazy()

    step = FillNullsStep(
        StepConfig(
            key="fill_nulls",
            parameters={
                "columns": ["value"],
                "value": 0,
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == [1, 0, 3]


def test_fill_nulls_replaces_nulls_in_multiple_columns():
    df = pl.DataFrame(
        {
            "a": [1, None, 3],
            "b": [None, 20, None],
        }
    ).lazy()

    step = FillNullsStep(
        StepConfig(
            key="fill_nulls",
            parameters={
                "columns": ["a", "b"],
                "value": 0,
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "a": [1, 0, 3],
        "b": [0, 20, 0],
    }


def test_fill_nulls_supports_string_fill_value():
    df = pl.DataFrame(
        {
            "name": ["A", None, "C"],
        }
    ).lazy()

    step = FillNullsStep(
        StepConfig(
            key="fill_nulls",
            parameters={
                "columns": ["name"],
                "value": "unknown",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["name"].to_list() == ["A", "unknown", "C"]


def test_fill_nulls_does_not_modify_unlisted_columns():
    df = pl.DataFrame(
        {
            "a": [1, None],
            "b": [10, None],
        }
    ).lazy()

    step = FillNullsStep(
        StepConfig(
            key="fill_nulls",
            parameters={
                "columns": ["a"],
                "value": 0,
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "a": [1, 0],
        "b": [10, None],
    }


def test_fill_nulls_returns_lazyframe():
    df = pl.DataFrame({"value": [1, None]}).lazy()

    step = FillNullsStep(
        StepConfig(
            key="fill_nulls",
            parameters={
                "columns": ["value"],
                "value": 0,
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_fill_nulls_rejects_missing_columns_parameter():
    with pytest.raises(ValidationError):
        FillNullsStep(
            StepConfig(
                key="fill_nulls",
                parameters={
                    "value": 0,
                },
            )
        )


def test_fill_nulls_rejects_missing_value_parameter():
    with pytest.raises(ValidationError):
        FillNullsStep(
            StepConfig(
                key="fill_nulls",
                parameters={
                    "columns": ["value"],
                },
            )
        )


def test_fill_nulls_raises_for_missing_dataframe_column():
    df = pl.DataFrame({"value": [1]}).lazy()

    step = FillNullsStep(
        StepConfig(
            key="fill_nulls",
            parameters={
                "columns": ["missing"],
                "value": 0,
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_fill_nulls_can_promote_column_type():
    df = pl.DataFrame(
        {
            "value": [1, None],
        }
    ).lazy()

    step = FillNullsStep(
        StepConfig(
            key="fill_nulls",
            parameters={
                "columns": ["value"],
                "value": "not-a-number",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == ["1", "not-a-number"]
        
def test_group_by_sums_values_by_single_column():
    df = pl.DataFrame(
        {
            "category": ["A", "A", "B", "B", "B"],
            "value": [10, 20, 5, 15, 25],
        }
    ).lazy()

    step = GroupByStep(
        StepConfig(
            key="group_by",
            parameters={
                "by": ["category"],
                "aggregations": [
                    {
                        "column": "value",
                        "function": "sum",
                        "alias": "total_value",
                    }
                ],
            },
        )
    )

    result = step.execute(df).collect().sort("category")

    assert result.to_dict(as_series=False) == {
        "category": ["A", "B"],
        "total_value": [30, 45],
    }


def test_group_by_supports_multiple_aggregations():
    df = pl.DataFrame(
        {
            "category": ["A", "A", "B", "B", "B"],
            "value": [10, 20, 5, 15, 25],
            "name": ["x", "y", "x", "x", "z"],
        }
    ).lazy()

    step = GroupByStep(
        StepConfig(
            key="group_by",
            parameters={
                "by": ["category"],
                "aggregations": [
                    {"column": "value", "function": "min", "alias": "min_value"},
                    {"column": "value", "function": "max", "alias": "max_value"},
                    {"column": "value", "function": "mean", "alias": "avg_value"},
                    {"column": "name", "function": "n_unique", "alias": "unique_names"},
                ],
            },
        )
    )

    result = step.execute(df).collect().sort("category")

    assert result.to_dict(as_series=False) == {
        "category": ["A", "B"],
        "min_value": [10, 5],
        "max_value": [20, 25],
        "avg_value": [15.0, 15.0],
        "unique_names": [2, 2],
    }


def test_group_by_supports_median():
    df = pl.DataFrame(
        {
            "category": ["A", "A", "A", "B", "B", "B"],
            "value": [10, 20, 30, 5, 15, 25],
        }
    ).lazy()

    step = GroupByStep(
        StepConfig(
            key="group_by",
            parameters={
                "by": ["category"],
                "aggregations": [
                    {
                        "column": "value",
                        "function": "median",
                        "alias": "median_value",
                    }
                ],
            },
        )
    )

    result = step.execute(df).collect().sort("category")

    assert result.to_dict(as_series=False) == {
        "category": ["A", "B"],
        "median_value": [20.0, 15.0],
    }


def test_group_by_supports_count():
    df = pl.DataFrame(
        {
            "category": ["A", "A", "B", "B", "B"],
            "value": [10, None, 5, 15, None],
        }
    ).lazy()

    step = GroupByStep(
        StepConfig(
            key="group_by",
            parameters={
                "by": ["category"],
                "aggregations": [
                    {
                        "column": "value",
                        "function": "count",
                        "alias": "value_count",
                    }
                ],
            },
        )
    )

    result = step.execute(df).collect().sort("category")

    assert result.to_dict(as_series=False) == {
        "category": ["A", "B"],
        "value_count": [1, 2],
    }


def test_group_by_supports_len():
    df = pl.DataFrame(
        {
            "category": ["A", "A", "B", "B", "B"],
            "value": [10, None, 5, 15, None],
        }
    ).lazy()

    step = GroupByStep(
        StepConfig(
            key="group_by",
            parameters={
                "by": ["category"],
                "aggregations": [
                    {
                        "column": "value",
                        "function": "len",
                        "alias": "row_count",
                    }
                ],
            },
        )
    )

    result = step.execute(df).collect().sort("category")

    assert result.to_dict(as_series=False) == {
        "category": ["A", "B"],
        "row_count": [2, 3],
    }


def test_group_by_supports_first_and_last():
    df = pl.DataFrame(
        {
            "category": ["A", "A", "B", "B", "B"],
            "value": [10, 20, 5, 15, 25],
        }
    ).lazy()

    step = GroupByStep(
        StepConfig(
            key="group_by",
            parameters={
                "by": ["category"],
                "aggregations": [
                    {"column": "value", "function": "first", "alias": "first_value"},
                    {"column": "value", "function": "last", "alias": "last_value"},
                ],
            },
        )
    )

    result = step.execute(df).collect().sort("category")

    assert result.to_dict(as_series=False) == {
        "category": ["A", "B"],
        "first_value": [10, 5],
        "last_value": [20, 25],
    }


def test_group_by_without_alias_uses_source_column_name():
    df = pl.DataFrame(
        {
            "category": ["A", "A", "B"],
            "value": [10, 20, 5],
        }
    ).lazy()

    step = GroupByStep(
        StepConfig(
            key="group_by",
            parameters={
                "by": ["category"],
                "aggregations": [
                    {
                        "column": "value",
                        "function": "sum",
                    }
                ],
            },
        )
    )

    result = step.execute(df).collect().sort("category")

    assert result.to_dict(as_series=False) == {
        "category": ["A", "B"],
        "value": [30, 5],
    }


def test_group_by_groups_by_multiple_columns():
    df = pl.DataFrame(
        {
            "country": ["PL", "PL", "PL", "DE"],
            "category": ["A", "A", "B", "A"],
            "value": [10, 20, 5, 100],
        }
    ).lazy()

    step = GroupByStep(
        StepConfig(
            key="group_by",
            parameters={
                "by": ["country", "category"],
                "aggregations": [
                    {
                        "column": "value",
                        "function": "sum",
                        "alias": "total",
                    }
                ],
            },
        )
    )

    result = step.execute(df).collect().sort(["country", "category"])

    assert result.to_dict(as_series=False) == {
        "country": ["DE", "PL", "PL"],
        "category": ["A", "A", "B"],
        "total": [100, 30, 5],
    }


def test_group_by_returns_lazyframe():
    df = pl.DataFrame(
        {
            "category": ["A"],
            "value": [10],
        }
    ).lazy()

    step = GroupByStep(
        StepConfig(
            key="group_by",
            parameters={
                "by": ["category"],
                "aggregations": [
                    {
                        "column": "value",
                        "function": "sum",
                        "alias": "total",
                    }
                ],
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_group_by_rejects_invalid_aggregation_function():
    with pytest.raises(ValidationError):
        GroupByStep(
            StepConfig(
                key="group_by",
                parameters={
                    "by": ["category"],
                    "aggregations": [
                        {
                            "column": "value",
                            "function": "average",
                            "alias": "avg_value",
                        }
                    ],
                },
            )
        )


def test_group_by_rejects_missing_by_parameter():
    with pytest.raises(ValidationError):
        GroupByStep(
            StepConfig(
                key="group_by",
                parameters={
                    "aggregations": [
                        {
                            "column": "value",
                            "function": "sum",
                            "alias": "total",
                        }
                    ],
                },
            )
        )


def test_group_by_rejects_missing_aggregations_parameter():
    with pytest.raises(ValidationError):
        GroupByStep(
            StepConfig(
                key="group_by",
                parameters={
                    "by": ["category"],
                },
            )
        )


def test_group_by_rejects_missing_aggregation_column():
    with pytest.raises(ValidationError):
        GroupByStep(
            StepConfig(
                key="group_by",
                parameters={
                    "by": ["category"],
                    "aggregations": [
                        {
                            "function": "sum",
                            "alias": "total",
                        }
                    ],
                },
            )
        )


def test_group_by_rejects_missing_aggregation_function():
    with pytest.raises(ValidationError):
        GroupByStep(
            StepConfig(
                key="group_by",
                parameters={
                    "by": ["category"],
                    "aggregations": [
                        {
                            "column": "value",
                            "alias": "total",
                        }
                    ],
                },
            )
        )


def test_group_by_raises_for_missing_group_column():
    df = pl.DataFrame(
        {
            "category": ["A"],
            "value": [10],
        }
    ).lazy()

    step = GroupByStep(
        StepConfig(
            key="group_by",
            parameters={
                "by": ["missing"],
                "aggregations": [
                    {
                        "column": "value",
                        "function": "sum",
                        "alias": "total",
                    }
                ],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_group_by_raises_for_missing_aggregation_column():
    df = pl.DataFrame(
        {
            "category": ["A"],
            "value": [10],
        }
    ).lazy()

    step = GroupByStep(
        StepConfig(
            key="group_by",
            parameters={
                "by": ["category"],
                "aggregations": [
                    {
                        "column": "missing",
                        "function": "sum",
                        "alias": "total",
                    }
                ],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()

def test_filter_rows_filters_equal_condition():
    df = pl.DataFrame(
        {
            "name": ["A", "B", "A"],
            "value": [1, 2, 3],
        }
    ).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "left": {"column": "name"},
                    "operator": "=",
                    "right": {"value": "A"},
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "name": ["A", "A"],
        "value": [1, 3],
    }


@pytest.mark.parametrize(
    ("operator", "expected_values"),
    [
        ("!=", [1, 3]),
        (">", [3]),
        (">=", [2, 3]),
        ("<", [1]),
        ("<=", [1, 2]),
    ],
)
def test_filter_rows_supports_basic_comparison_operators(operator, expected_values):
    df = pl.DataFrame({"value": [1, 2, 3]}).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "left": {"column": "value"},
                    "operator": operator,
                    "right": {"value": 2},
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == expected_values


@pytest.mark.parametrize(
    ("operator", "expected_names"),
    [
        ("contains", ["alpha", "alphabet"]),
        ("starts_with", ["alpha", "alphabet"]),
        ("ends_with", ["beta"]),
    ],
)
def test_filter_rows_supports_string_operators(operator, expected_names):
    df = pl.DataFrame(
        {
            "name": ["alpha", "beta", "alphabet", "gamma"],
        }
    ).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "left": {"column": "name"},
                    "operator": operator,
                    "right": {"value": "alpha" if operator != "ends_with" else "ta"},
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result["name"].to_list() == expected_names


def test_filter_rows_supports_is_null():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "value": [10, None, None],
        }
    ).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "left": {"column": "value"},
                    "operator": "is_null",
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result["id"].to_list() == [2, 3]


def test_filter_rows_supports_is_not_null():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "value": [10, None, None],
        }
    ).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "left": {"column": "value"},
                    "operator": "is_not_null",
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result["id"].to_list() == [1]


def test_filter_rows_supports_is_in():
    df = pl.DataFrame(
        {
            "name": ["A", "B", "C", "D"],
        }
    ).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "left": {"column": "name"},
                    "operator": "is_in",
                    "right": {"value": ["A", "C"]},
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result["name"].to_list() == ["A", "C"]


def test_filter_rows_supports_and_condition():
    df = pl.DataFrame(
        {
            "name": ["A", "A", "B", "B"],
            "value": [1, 3, 2, 4],
        }
    ).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "logic": "and",
                    "conditions": [
                        {
                            "left": {"column": "name"},
                            "operator": "=",
                            "right": {"value": "A"},
                        },
                        {
                            "left": {"column": "value"},
                            "operator": ">",
                            "right": {"value": 2},
                        },
                    ],
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "name": ["A"],
        "value": [3],
    }


def test_filter_rows_supports_or_condition():
    df = pl.DataFrame(
        {
            "name": ["A", "B", "C"],
            "value": [1, 2, 3],
        }
    ).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "logic": "or",
                    "conditions": [
                        {
                            "left": {"column": "name"},
                            "operator": "=",
                            "right": {"value": "A"},
                        },
                        {
                            "left": {"column": "value"},
                            "operator": ">",
                            "right": {"value": 2},
                        },
                    ],
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "name": ["A", "C"],
        "value": [1, 3],
    }


def test_filter_rows_supports_not_condition():
    df = pl.DataFrame(
        {
            "name": ["A", "B", "C"],
        }
    ).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "logic": "not",
                    "condition": {
                        "left": {"column": "name"},
                        "operator": "=",
                        "right": {"value": "A"},
                    },
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result["name"].to_list() == ["B", "C"]


def test_filter_rows_supports_expression_on_left_side():
    df = pl.DataFrame(
        {
            "a": [1, 2, 3],
            "b": [10, 20, 30],
        }
    ).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "left": {
                        "op": "add",
                        "args": [
                            {"column": "a"},
                            {"column": "b"},
                        ],
                    },
                    "operator": ">",
                    "right": {"value": 22},
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "a": [3],
        "b": [30],
    }


def test_filter_rows_returns_lazyframe():
    df = pl.DataFrame({"value": [1, 2]}).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "left": {"column": "value"},
                    "operator": ">",
                    "right": {"value": 1},
                },
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_filter_rows_rejects_missing_condition():
    with pytest.raises(ValidationError):
        FilterRowsStep(
            StepConfig(
                key="filter_rows",
                parameters={},
            )
        )


def test_filter_rows_rejects_invalid_operator():
    with pytest.raises(ValidationError):
        FilterRowsStep(
            StepConfig(
                key="filter_rows",
                parameters={
                    "condition": {
                        "left": {"column": "value"},
                        "operator": "between",
                        "right": {"value": 1},
                    },
                },
            )
        )


def test_filter_rows_raises_when_operator_requires_right_expression():
    df = pl.DataFrame({"value": [1, 2]}).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "left": {"column": "value"},
                    "operator": "=",
                },
            },
        )
    )

    with pytest.raises(ValueError):
        step.execute(df).collect()


def test_filter_rows_raises_for_empty_and_condition():
    df = pl.DataFrame({"value": [1, 2]}).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "logic": "and",
                    "conditions": [],
                },
            },
        )
    )

    with pytest.raises(ValueError):
        step.execute(df).collect()


def test_filter_rows_raises_for_empty_or_condition():
    df = pl.DataFrame({"value": [1, 2]}).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "logic": "or",
                    "conditions": [],
                },
            },
        )
    )

    with pytest.raises(ValueError):
        step.execute(df).collect()


def test_filter_rows_raises_for_missing_dataframe_column():
    df = pl.DataFrame({"value": [1, 2]}).lazy()

    step = FilterRowsStep(
        StepConfig(
            key="filter_rows",
            parameters={
                "condition": {
                    "left": {"column": "missing"},
                    "operator": "=",
                    "right": {"value": 1},
                },
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_join_left_joins_right_input_from_context():
    left = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
        }
    ).lazy()

    right = pl.DataFrame(
        {
            "id": [1, 2],
            "score": [100, 200],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "id",
                "right_on": "id",
                "how": "left",
            },
        )
    )

    result = step.execute(left, context).collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": [1, 2, 3],
        "name": ["A", "B", "C"],
        "score": [100, 200, None],
    }


def test_join_uses_left_join_by_default():
    left = pl.DataFrame({"id": [1, 2]}).lazy()
    right = pl.DataFrame({"id": [1], "score": [100]}).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "id",
                "right_on": "id",
            },
        )
    )

    result = step.execute(left, context).collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "score": [100, None],
    }


def test_join_inner_keeps_only_matching_rows():
    left = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
        }
    ).lazy()

    right = pl.DataFrame(
        {
            "id": [1, 3, 4],
            "score": [100, 300, 400],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "id",
                "right_on": "id",
                "how": "inner",
            },
        )
    )

    result = step.execute(left, context).collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": [1, 3],
        "name": ["A", "C"],
        "score": [100, 300],
    }


def test_join_right_keeps_all_right_rows():
    left = pl.DataFrame(
        {
            "id": [1, 2],
            "name": ["A", "B"],
        }
    ).lazy()

    right = pl.DataFrame(
        {
            "id": [1, 3],
            "score": [100, 300],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "id",
                "right_on": "id",
                "how": "right",
            },
        )
    )

    result = step.execute(left, context).collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "name": ["A", None],
        "id": [1, 3],
        "score": [100, 300],
    }


def test_join_full_keeps_rows_from_both_sides():
    left = pl.DataFrame(
        {
            "id": [1, 2],
            "name": ["A", "B"],
        }
    ).lazy()

    right = pl.DataFrame(
        {
            "id": [1, 3],
            "score": [100, 300],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "id",
                "right_on": "id",
                "how": "full",
            },
        )
    )

    result = step.execute(left, context).collect().sort("id", nulls_last=True)

    assert result["id"].to_list() == [1, 2, None]
    assert result["id_right"].to_list() == [1, None, 3]
    assert result["name"].to_list() == ["A", "B", None]
    assert result["score"].to_list() == [100, None, 300]


def test_join_anti_keeps_only_left_rows_without_match():
    left = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
        }
    ).lazy()

    right = pl.DataFrame(
        {
            "id": [1, 3],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "id",
                "right_on": "id",
                "how": "anti",
            },
        )
    )

    result = step.execute(left, context).collect()

    assert result.to_dict(as_series=False) == {
        "id": [2],
        "name": ["B"],
    }


def test_join_cross_creates_cartesian_product():
    left = pl.DataFrame(
        {
            "left_id": [1, 2],
        }
    ).lazy()

    right = pl.DataFrame(
        {
            "right_id": ["A", "B"],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "left_id",
                "right_on": "right_id",
                "how": "cross",
            },
        )
    )

    result = step.execute(left, context).collect().sort(["left_id", "right_id"])

    assert result.to_dict(as_series=False) == {
        "left_id": [1, 1, 2, 2],
        "right_id": ["A", "B", "A", "B"],
    }


def test_join_supports_different_key_column_names():
    left = pl.DataFrame(
        {
            "customer_id": [1, 2],
            "name": ["A", "B"],
        }
    ).lazy()

    right = pl.DataFrame(
        {
            "id": [1, 2],
            "score": [100, 200],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "customer_id",
                "right_on": "id",
                "how": "inner",
            },
        )
    )

    result = step.execute(left, context).collect().sort("customer_id")

    assert result.to_dict(as_series=False) == {
        "customer_id": [1, 2],
        "name": ["A", "B"],
        "score": [100, 200],
    }


def test_join_supports_multiple_key_columns():
    left = pl.DataFrame(
        {
            "country": ["PL", "PL", "DE"],
            "id": [1, 2, 1],
            "name": ["A", "B", "C"],
        }
    ).lazy()

    right = pl.DataFrame(
        {
            "country": ["PL", "DE"],
            "id": [1, 1],
            "score": [100, 300],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": ["country", "id"],
                "right_on": ["country", "id"],
                "how": "left",
            },
        )
    )

    result = step.execute(left, context).collect().sort(["country", "id"])

    assert result.to_dict(as_series=False) == {
        "country": ["DE", "PL", "PL"],
        "id": [1, 1, 2],
        "name": ["C", "A", "B"],
        "score": [300, 100, None],
    }


def test_join_removes_right_input_from_context_after_execution():
    left = pl.DataFrame({"id": [1]}).lazy()
    right = pl.DataFrame({"id": [1], "score": [100]}).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "id",
                "right_on": "id",
            },
        )
    )

    step.execute(left, context)

    assert context.extra_inputs == {}


def test_join_returns_lazyframe():
    left = pl.DataFrame({"id": [1]}).lazy()
    right = pl.DataFrame({"id": [1], "score": [100]}).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "id",
                "right_on": "id",
            },
        )
    )

    result = step.execute(left, context)

    assert isinstance(result, pl.LazyFrame)


def test_join_rejects_invalid_how_value():
    with pytest.raises(ValidationError):
        JoinStep(
            StepConfig(
                key="join",
                parameters={
                    "left_on": "id",
                    "right_on": "id",
                    "how": "outer",
                },
            )
        )


def test_join_rejects_missing_left_on_parameter():
    with pytest.raises(ValidationError):
        JoinStep(
            StepConfig(
                key="join",
                parameters={
                    "right_on": "id",
                },
            )
        )


def test_join_rejects_missing_right_on_parameter():
    with pytest.raises(ValidationError):
        JoinStep(
            StepConfig(
                key="join",
                parameters={
                    "left_on": "id",
                },
            )
        )


def test_join_fails_without_context():
    left = pl.DataFrame({"id": [1]}).lazy()

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "id",
                "right_on": "id",
            },
        )
    )

    with pytest.raises(ValueError):
        step.execute(left, None)


def test_join_fails_when_context_has_no_right_input():
    left = pl.DataFrame({"id": [1]}).lazy()

    context = StepExecutionContext(extra_inputs={})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "id",
                "right_on": "id",
            },
        )
    )

    with pytest.raises(ValueError):
        step.execute(left, context)


def test_join_raises_for_missing_left_column():
    left = pl.DataFrame({"id": [1]}).lazy()
    right = pl.DataFrame({"id": [1]}).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "missing",
                "right_on": "id",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(left, context).collect()


def test_join_raises_for_missing_right_column():
    left = pl.DataFrame({"id": [1]}).lazy()
    right = pl.DataFrame({"id": [1]}).lazy()

    context = StepExecutionContext(extra_inputs={"right": right})

    step = JoinStep(
        StepConfig(
            key="join",
            parameters={
                "left_on": "id",
                "right_on": "missing",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(left, context).collect()
        
def test_limit_rows_head_keeps_first_n_rows():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "name": ["A", "B", "C", "D"],
        }
    ).lazy()

    step = LimitRowsStep(
        StepConfig(
            key="limit_rows",
            parameters={
                "limit": 2,
                "mode": "head",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", "B"],
    }


def test_limit_rows_tail_keeps_last_n_rows():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "name": ["A", "B", "C", "D"],
        }
    ).lazy()

    step = LimitRowsStep(
        StepConfig(
            key="limit_rows",
            parameters={
                "limit": 2,
                "mode": "tail",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [3, 4],
        "name": ["C", "D"],
    }


def test_limit_rows_limit_larger_than_dataframe_keeps_all_rows():
    df = pl.DataFrame(
        {
            "id": [1, 2],
        }
    ).lazy()

    step = LimitRowsStep(
        StepConfig(
            key="limit_rows",
            parameters={
                "limit": 10,
                "mode": "head",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["id"].to_list() == [1, 2]


def test_limit_rows_zero_returns_empty_dataframe():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
        }
    ).lazy()

    step = LimitRowsStep(
        StepConfig(
            key="limit_rows",
            parameters={
                "limit": 0,
                "mode": "head",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.height == 0


def test_limit_rows_returns_lazyframe():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
        }
    ).lazy()

    step = LimitRowsStep(
        StepConfig(
            key="limit_rows",
            parameters={
                "limit": 1,
                "mode": "head",
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_limit_rows_rejects_invalid_mode():
    with pytest.raises(ValidationError):
        LimitRowsStep(
            StepConfig(
                key="limit_rows",
                parameters={
                    "limit": 2,
                    "mode": "middle",
                },
            )
        )


def test_limit_rows_rejects_missing_limit():
    with pytest.raises(ValidationError):
        LimitRowsStep(
            StepConfig(
                key="limit_rows",
                parameters={
                    "mode": "head",
                },
            )
        )


def test_limit_rows_rejects_missing_mode():
    with pytest.raises(ValidationError):
        LimitRowsStep(
            StepConfig(
                key="limit_rows",
                parameters={
                    "limit": 2,
                },
            )
        )
        
def test_parse_datetime_parses_date_column_in_place():
    df = pl.DataFrame(
        {
            "date_text": ["2026-06-09", "2026-06-10"],
        }
    ).lazy()

    step = ParseDateTimeStep(
        StepConfig(
            key="parse_datetime",
            parameters={
                "column": "date_text",
                "target_type": "date",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.schema["date_text"] == pl.Date
    assert result["date_text"].to_list() == [
        date(2026, 6, 9),
        date(2026, 6, 10),
    ]


def test_parse_datetime_parses_datetime_column_in_place():
    df = pl.DataFrame(
        {
            "dt_text": ["2026-06-09 13:45:30"],
        }
    ).lazy()

    step = ParseDateTimeStep(
        StepConfig(
            key="parse_datetime",
            parameters={
                "column": "dt_text",
                "target_type": "datetime",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.schema["dt_text"] == pl.Datetime
    assert result["dt_text"].to_list() == [
        datetime(2026, 6, 9, 13, 45, 30),
    ]


def test_parse_datetime_parses_time_column_in_place():
    df = pl.DataFrame(
        {
            "time_text": ["13:45:30"],
        }
    ).lazy()

    step = ParseDateTimeStep(
        StepConfig(
            key="parse_datetime",
            parameters={
                "column": "time_text",
                "target_type": "time",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.schema["time_text"] == pl.Time
    assert result["time_text"].to_list() == [
        time(13, 45, 30),
    ]


def test_parse_datetime_uses_custom_format():
    df = pl.DataFrame(
        {
            "date_text": ["09/06/2026"],
        }
    ).lazy()

    step = ParseDateTimeStep(
        StepConfig(
            key="parse_datetime",
            parameters={
                "column": "date_text",
                "target_type": "date",
                "format": "%d/%m/%Y",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.schema["date_text"] == pl.Date
    assert result["date_text"].to_list() == [
        date(2026, 6, 9),
    ]


def test_parse_datetime_writes_to_output_column():
    df = pl.DataFrame(
        {
            "date_text": ["2026-06-09"],
        }
    ).lazy()

    step = ParseDateTimeStep(
        StepConfig(
            key="parse_datetime",
            parameters={
                "column": "date_text",
                "target_type": "date",
                "output_column": "parsed_date",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.columns == ["date_text", "parsed_date"]
    assert result.schema["date_text"] == pl.String
    assert result.schema["parsed_date"] == pl.Date
    assert result.to_dict(as_series=False) == {
        "date_text": ["2026-06-09"],
        "parsed_date": [date(2026, 6, 9)],
    }


def test_parse_datetime_strict_false_converts_invalid_values_to_null():
    df = pl.DataFrame(
        {
            "date_text": ["2026-06-09", "not-a-date"],
        }
    ).lazy()

    step = ParseDateTimeStep(
        StepConfig(
            key="parse_datetime",
            parameters={
                "column": "date_text",
                "target_type": "date",
                "strict": False,
            },
        )
    )

    result = step.execute(df).collect()

    assert result["date_text"].to_list() == [
        date(2026, 6, 9),
        None,
    ]


def test_parse_datetime_strict_true_raises_for_invalid_value():
    df = pl.DataFrame(
        {
            "date_text": ["2026-06-09", "not-a-date"],
        }
    ).lazy()

    step = ParseDateTimeStep(
        StepConfig(
            key="parse_datetime",
            parameters={
                "column": "date_text",
                "target_type": "date",
                "strict": True,
            },
        )
    )

    with pytest.raises(pl.exceptions.InvalidOperationError):
        step.execute(df).collect()


def test_parse_datetime_returns_lazyframe():
    df = pl.DataFrame(
        {
            "date_text": ["2026-06-09"],
        }
    ).lazy()

    step = ParseDateTimeStep(
        StepConfig(
            key="parse_datetime",
            parameters={
                "column": "date_text",
                "target_type": "date",
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_parse_datetime_rejects_invalid_target_type():
    with pytest.raises(ValidationError):
        ParseDateTimeStep(
            StepConfig(
                key="parse_datetime",
                parameters={
                    "column": "date_text",
                    "target_type": "timestamp",
                },
            )
        )


def test_parse_datetime_rejects_missing_column_parameter():
    with pytest.raises(ValidationError):
        ParseDateTimeStep(
            StepConfig(
                key="parse_datetime",
                parameters={
                    "target_type": "date",
                },
            )
        )


def test_parse_datetime_rejects_missing_target_type_parameter():
    with pytest.raises(ValidationError):
        ParseDateTimeStep(
            StepConfig(
                key="parse_datetime",
                parameters={
                    "column": "date_text",
                },
            )
        )


def test_parse_datetime_raises_for_missing_dataframe_column():
    df = pl.DataFrame(
        {
            "date_text": ["2026-06-09"],
        }
    ).lazy()

    step = ParseDateTimeStep(
        StepConfig(
            key="parse_datetime",
            parameters={
                "column": "missing",
                "target_type": "date",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_pivot_pivots_single_value_column():
    df = pl.DataFrame(
        {
            "id": [1, 1, 2, 2],
            "metric": ["height", "weight", "height", "weight"],
            "value": [180, 80, 170, 70],
        }
    ).lazy()

    step = PivotStep(
        StepConfig(
            key="pivot",
            parameters={
                "on": ["metric"],
                "index": ["id"],
                "values": ["value"],
                "aggregate_function": "first",
            },
        )
    )

    result = step.execute(df).collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "height": [180, 170],
        "weight": [80, 70],
    }


def test_pivot_uses_first_aggregation_by_default():
    df = pl.DataFrame(
        {
            "id": [1, 1],
            "metric": ["height", "weight"],
            "value": [180, 80],
        }
    ).lazy()

    step = PivotStep(
        StepConfig(
            key="pivot",
            parameters={
                "on": ["metric"],
                "index": ["id"],
                "values": ["value"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "height": [180],
        "weight": [80],
    }


def test_pivot_sums_duplicate_combinations():
    df = pl.DataFrame(
        {
            "id": [1, 1, 1, 2],
            "metric": ["sales", "sales", "cost", "sales"],
            "value": [10, 20, 5, 100],
        }
    ).lazy()

    step = PivotStep(
        StepConfig(
            key="pivot",
            parameters={
                "on": ["metric"],
                "index": ["id"],
                "values": ["value"],
                "aggregate_function": "sum",
            },
        )
    )

    result = step.execute(df).collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "sales": [30, 100],
        "cost": [5, 0],
    }


def test_pivot_supports_multiple_index_columns():
    df = pl.DataFrame(
        {
            "country": ["PL", "PL", "DE", "DE"],
            "id": [1, 1, 1, 1],
            "metric": ["height", "weight", "height", "weight"],
            "value": [180, 80, 175, 75],
        }
    ).lazy()

    step = PivotStep(
        StepConfig(
            key="pivot",
            parameters={
                "on": ["metric"],
                "index": ["country", "id"],
                "values": ["value"],
                "aggregate_function": "first",
            },
        )
    )

    result = step.execute(df).collect().sort(["country", "id"])

    assert result.to_dict(as_series=False) == {
        "country": ["DE", "PL"],
        "id": [1, 1],
        "height": [175, 180],
        "weight": [75, 80],
    }


def test_pivot_supports_multiple_value_columns():
    df = pl.DataFrame(
        {
            "id": [1, 1, 2, 2],
            "metric": ["height", "weight", "height", "weight"],
            "value": [180, 80, 170, 70],
            "quality": [1, 2, 3, 4],
        }
    ).lazy()

    step = PivotStep(
        StepConfig(
            key="pivot",
            parameters={
                "on": ["metric"],
                "index": ["id"],
                "values": ["value", "quality"],
                "aggregate_function": "first",
            },
        )
    )

    result = step.execute(df).collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "value_height": [180, 170],
        "value_weight": [80, 70],
        "quality_height": [1, 3],
        "quality_weight": [2, 4],
    }


@pytest.mark.parametrize(
    ("aggregate_function", "expected_sales"),
    [
        ("first", 10),
        ("last", 20),
        ("sum", 30),
        ("min", 10),
        ("max", 20),
        ("mean", 15.0),
        ("median", 15.0),
        ("len", 2),
    ],
)
def test_pivot_supports_declared_aggregate_functions(
    aggregate_function,
    expected_sales,
):
    df = pl.DataFrame(
        {
            "id": [1, 1],
            "metric": ["sales", "sales"],
            "value": [10, 20],
        }
    ).lazy()

    step = PivotStep(
        StepConfig(
            key="pivot",
            parameters={
                "on": ["metric"],
                "index": ["id"],
                "values": ["value"],
                "aggregate_function": aggregate_function,
            },
        )
    )

    result = step.execute(df).collect()

    assert result["sales"].to_list() == [expected_sales]


def test_pivot_returns_lazyframe():
    df = pl.DataFrame(
        {
            "id": [1],
            "metric": ["height"],
            "value": [180],
        }
    ).lazy()

    step = PivotStep(
        StepConfig(
            key="pivot",
            parameters={
                "on": ["metric"],
                "index": ["id"],
                "values": ["value"],
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_pivot_rejects_invalid_aggregate_function():
    with pytest.raises(ValidationError):
        PivotStep(
            StepConfig(
                key="pivot",
                parameters={
                    "on": ["metric"],
                    "index": ["id"],
                    "values": ["value"],
                    "aggregate_function": "count",
                },
            )
        )


def test_pivot_rejects_missing_on_parameter():
    with pytest.raises(ValidationError):
        PivotStep(
            StepConfig(
                key="pivot",
                parameters={
                    "index": ["id"],
                    "values": ["value"],
                },
            )
        )


def test_pivot_rejects_missing_index_parameter():
    with pytest.raises(ValidationError):
        PivotStep(
            StepConfig(
                key="pivot",
                parameters={
                    "on": ["metric"],
                    "values": ["value"],
                },
            )
        )


def test_pivot_rejects_missing_values_parameter():
    with pytest.raises(ValidationError):
        PivotStep(
            StepConfig(
                key="pivot",
                parameters={
                    "on": ["metric"],
                    "index": ["id"],
                },
            )
        )


def test_pivot_raises_for_missing_on_column():
    df = pl.DataFrame(
        {
            "id": [1],
            "metric": ["height"],
            "value": [180],
        }
    ).lazy()

    step = PivotStep(
        StepConfig(
            key="pivot",
            parameters={
                "on": ["missing"],
                "index": ["id"],
                "values": ["value"],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_pivot_raises_for_missing_index_column():
    df = pl.DataFrame(
        {
            "id": [1],
            "metric": ["height"],
            "value": [180],
        }
    ).lazy()

    step = PivotStep(
        StepConfig(
            key="pivot",
            parameters={
                "on": ["metric"],
                "index": ["missing"],
                "values": ["value"],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_pivot_raises_for_missing_values_column():
    df = pl.DataFrame(
        {
            "id": [1],
            "metric": ["height"],
            "value": [180],
        }
    ).lazy()

    step = PivotStep(
        StepConfig(
            key="pivot",
            parameters={
                "on": ["metric"],
                "index": ["id"],
                "values": ["missing"],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_read_csv_reads_file_with_default_separator(tmp_path):
    csv_path = tmp_path / "input.csv"
    csv_path.write_text(
        "id,name\n1,A\n2,B\n",
        encoding="utf-8",
    )

    step = ReadCsvStep(
        StepConfig(
            key="read_csv",
            parameters={
                "path": csv_path,
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": ["1", "2"],
        "name": ["A", "B"],
    }


def test_read_csv_reads_file_with_custom_separator(tmp_path):
    csv_path = tmp_path / "input.csv"
    csv_path.write_text(
        "id;name\n1;A\n2;B\n",
        encoding="utf-8",
    )

    step = ReadCsvStep(
        StepConfig(
            key="read_csv",
            parameters={
                "path": csv_path,
                "separator": ";",
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": ["1", "2"],
        "name": ["A", "B"],
    }


def test_read_csv_returns_lazyframe(tmp_path):
    csv_path = tmp_path / "input.csv"
    csv_path.write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )

    step = ReadCsvStep(
        StepConfig(
            key="read_csv",
            parameters={
                "path": csv_path,
            },
        )
    )

    result = step.execute()

    assert isinstance(result, pl.LazyFrame)


def test_read_csv_stores_result_in_context_when_enabled(tmp_path):
    csv_path = tmp_path / "input.csv"
    csv_path.write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )

    context = StepExecutionContext(extra_inputs={})

    step = ReadCsvStep(
        StepConfig(
            key="read_csv",
            parameters={
                "path": csv_path,
                "context_store": True,
                "context_key": "csv_input",
            },
        )
    )

    result = step.execute(context=context)

    assert "csv_input" in context.extra_inputs
    assert isinstance(context.extra_inputs["csv_input"], pl.LazyFrame)
    assert context.extra_inputs["csv_input"].collect().to_dict(as_series=False) == {
        "id": ["1"],
        "name": ["A"],
    }
    assert result.collect().to_dict(as_series=False) == {
        "id": ["1"],
        "name": ["A"],
    }


def test_read_csv_does_not_store_result_in_context_by_default(tmp_path):
    csv_path = tmp_path / "input.csv"
    csv_path.write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )

    context = StepExecutionContext(extra_inputs={})

    step = ReadCsvStep(
        StepConfig(
            key="read_csv",
            parameters={
                "path": csv_path,
            },
        )
    )

    step.execute(context=context)

    assert context.extra_inputs == {}


def test_read_csv_returns_existing_data_when_data_is_provided(tmp_path):
    csv_path = tmp_path / "input.csv"
    csv_path.write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )

    existing_data = pl.DataFrame(
        {
            "existing": [100],
        }
    ).lazy()

    step = ReadCsvStep(
        StepConfig(
            key="read_csv",
            parameters={
                "path": csv_path,
            },
        )
    )

    result = step.execute(data=existing_data).collect()

    assert result.to_dict(as_series=False) == {
        "existing": [100],
    }


def test_read_csv_still_reads_and_stores_when_existing_data_is_provided(tmp_path):
    csv_path = tmp_path / "input.csv"
    csv_path.write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )

    existing_data = pl.DataFrame(
        {
            "existing": [100],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={})

    step = ReadCsvStep(
        StepConfig(
            key="read_csv",
            parameters={
                "path": csv_path,
                "context_store": True,
                "context_key": "csv_input",
            },
        )
    )

    result = step.execute(data=existing_data, context=context).collect()

    assert result.to_dict(as_series=False) == {
        "existing": [100],
    }
    assert context.extra_inputs["csv_input"].collect().to_dict(as_series=False) == {
        "id": ["1"],
        "name": ["A"],
    }


def test_read_csv_rejects_missing_path_parameter():
    with pytest.raises(ValidationError):
        ReadCsvStep(
            StepConfig(
                key="read_csv",
                parameters={},
            )
        )


def test_read_csv_raises_for_missing_file(tmp_path):
    missing_path = tmp_path / "missing.csv"

    step = ReadCsvStep(
        StepConfig(
            key="read_csv",
            parameters={
                "path": missing_path,
            },
        )
    )

    with pytest.raises(FileNotFoundError):
        step.execute().collect()
        
def test_read_excel_reads_default_sheet(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pl.DataFrame(
        {
            "id": [1, 2],
            "name": ["A", "B"],
        }
    ).write_excel(excel_path)

    step = ReadExcelStep(
        StepConfig(
            key="read_excel",
            parameters={
                "path": excel_path,
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", "B"],
    }


def test_read_excel_reads_selected_sheet(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    with pd.ExcelWriter(excel_path) as writer:
        pd.DataFrame(
            {
                "id": [1],
                "name": ["A"],
            }
        ).to_excel(writer, sheet_name="first", index=False)

        pd.DataFrame(
            {
                "id": [2],
                "name": ["B"],
            }
        ).to_excel(writer, sheet_name="second", index=False)

    step = ReadExcelStep(
        StepConfig(
            key="read_excel",
            parameters={
                "path": excel_path,
                "sheet": "second",
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": [2],
        "name": ["B"],
    }


def test_read_excel_returns_lazyframe(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pl.DataFrame(
        {
            "id": [1],
        }
    ).write_excel(excel_path)

    step = ReadExcelStep(
        StepConfig(
            key="read_excel",
            parameters={
                "path": excel_path,
            },
        )
    )

    result = step.execute()

    assert isinstance(result, pl.LazyFrame)


def test_read_excel_stores_result_in_context_when_enabled(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pl.DataFrame(
        {
            "id": [1],
            "name": ["A"],
        }
    ).write_excel(excel_path)

    context = StepExecutionContext(extra_inputs={})

    step = ReadExcelStep(
        StepConfig(
            key="read_excel",
            parameters={
                "path": excel_path,
                "context_store": True,
                "context_key": "excel_input",
            },
        )
    )

    result = step.execute(context=context)

    assert "excel_input" in context.extra_inputs
    assert isinstance(context.extra_inputs["excel_input"], pl.LazyFrame)
    assert context.extra_inputs["excel_input"].collect().to_dict(as_series=False) == {
        "id": [1],
        "name": ["A"],
    }
    assert result.collect().to_dict(as_series=False) == {
        "id": [1],
        "name": ["A"],
    }


def test_read_excel_does_not_store_result_in_context_by_default(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pl.DataFrame(
        {
            "id": [1],
        }
    ).write_excel(excel_path)

    context = StepExecutionContext(extra_inputs={})

    step = ReadExcelStep(
        StepConfig(
            key="read_excel",
            parameters={
                "path": excel_path,
            },
        )
    )

    step.execute(context=context)

    assert context.extra_inputs == {}


def test_read_excel_returns_existing_data_when_data_is_provided(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pl.DataFrame(
        {
            "id": [1],
        }
    ).write_excel(excel_path)

    existing_data = pl.DataFrame(
        {
            "existing": [100],
        }
    ).lazy()

    step = ReadExcelStep(
        StepConfig(
            key="read_excel",
            parameters={
                "path": excel_path,
            },
        )
    )

    result = step.execute(data=existing_data).collect()

    assert result.to_dict(as_series=False) == {
        "existing": [100],
    }


def test_read_excel_still_reads_and_stores_when_existing_data_is_provided(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pl.DataFrame(
        {
            "id": [1],
            "name": ["A"],
        }
    ).write_excel(excel_path)

    existing_data = pl.DataFrame(
        {
            "existing": [100],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={})

    step = ReadExcelStep(
        StepConfig(
            key="read_excel",
            parameters={
                "path": excel_path,
                "context_store": True,
                "context_key": "excel_input",
            },
        )
    )

    result = step.execute(data=existing_data, context=context).collect()

    assert result.to_dict(as_series=False) == {
        "existing": [100],
    }
    assert context.extra_inputs["excel_input"].collect().to_dict(as_series=False) == {
        "id": [1],
        "name": ["A"],
    }


def test_read_excel_rejects_missing_path_parameter():
    with pytest.raises(ValidationError):
        ReadExcelStep(
            StepConfig(
                key="read_excel",
                parameters={},
            )
        )


def test_read_excel_raises_for_missing_file(tmp_path):
    missing_path = tmp_path / "missing.xlsx"

    step = ReadExcelStep(
        StepConfig(
            key="read_excel",
            parameters={
                "path": missing_path,
            },
        )
    )

    with pytest.raises(FileNotFoundError):
        step.execute().collect()
        
def test_read_folder_csv_reads_and_concatenates_csv_files(tmp_path):
    (tmp_path / "first.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )
    (tmp_path / "second.csv").write_text(
        "id,name\n2,B\n",
        encoding="utf-8",
    )

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
            },
        )
    )

    result = step.execute().collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": ["1", "2"],
        "name": ["A", "B"],
        "source_file": ["first.csv", "second.csv"],
    }


def test_read_folder_csv_uses_custom_pattern(tmp_path):
    (tmp_path / "keep.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )
    (tmp_path / "skip.txt").write_text(
        "id,name\n2,B\n",
        encoding="utf-8",
    )

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
                "pattern": "*.csv",
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": ["1"],
        "name": ["A"],
        "source_file": ["keep.csv"],
    }


def test_read_folder_csv_reads_custom_separator(tmp_path):
    (tmp_path / "first.csv").write_text(
        "id;name\n1;A\n",
        encoding="utf-8",
    )
    (tmp_path / "second.csv").write_text(
        "id;name\n2;B\n",
        encoding="utf-8",
    )

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
                "separator": ";",
            },
        )
    )

    result = step.execute().collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": ["1", "2"],
        "name": ["A", "B"],
        "source_file": ["first.csv", "second.csv"],
    }


def test_read_folder_csv_can_disable_source_file_column(tmp_path):
    (tmp_path / "first.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )
    (tmp_path / "second.csv").write_text(
        "id,name\n2,B\n",
        encoding="utf-8",
    )

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
                "add_source_file": False,
            },
        )
    )

    result = step.execute().collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": ["1", "2"],
        "name": ["A", "B"],
    }


def test_read_folder_csv_uses_custom_source_column(tmp_path):
    (tmp_path / "first.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
                "source_column": "file_name",
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": ["1"],
        "name": ["A"],
        "file_name": ["first.csv"],
    }


def test_read_folder_csv_supports_recursive_search(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()

    (tmp_path / "root.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )
    (nested / "nested.csv").write_text(
        "id,name\n2,B\n",
        encoding="utf-8",
    )

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
                "recursive": True,
            },
        )
    )

    result = step.execute().collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": ["1", "2"],
        "name": ["A", "B"],
        "source_file": ["root.csv", "nested.csv"],
    }


def test_read_folder_csv_non_recursive_ignores_nested_files(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()

    (tmp_path / "root.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )
    (nested / "nested.csv").write_text(
        "id,name\n2,B\n",
        encoding="utf-8",
    )

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
                "recursive": False,
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": ["1"],
        "name": ["A"],
        "source_file": ["root.csv"],
    }


def test_read_folder_csv_concatenates_different_schemas_diagonally(tmp_path):
    (tmp_path / "first.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )
    (tmp_path / "second.csv").write_text(
        "id,score\n2,100\n",
        encoding="utf-8",
    )

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
            },
        )
    )

    result = step.execute().collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": ["1", "2"],
        "name": ["A", None],
        "source_file": ["first.csv", "second.csv"],
        "score": [None, "100"],
    }


def test_read_folder_csv_can_infer_types(tmp_path):
    (tmp_path / "first.csv").write_text(
        "id,value\n1,10\n",
        encoding="utf-8",
    )
    (tmp_path / "second.csv").write_text(
        "id,value\n2,20\n",
        encoding="utf-8",
    )

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
                "infer_types": True,
            },
        )
    )

    result = step.execute().collect().sort("id")

    assert result.schema["id"] == pl.Int64
    assert result.schema["value"] == pl.Int64
    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "value": [10, 20],
        "source_file": ["first.csv", "second.csv"],
    }


def test_read_folder_csv_stores_result_in_context_when_enabled(tmp_path):
    (tmp_path / "first.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )

    context = StepExecutionContext(extra_inputs={})

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
                "context_store": True,
                "context_key": "folder_csv",
            },
        )
    )

    result = step.execute(context=context)

    assert "folder_csv" in context.extra_inputs
    assert isinstance(context.extra_inputs["folder_csv"], pl.LazyFrame)
    assert context.extra_inputs["folder_csv"].collect().to_dict(as_series=False) == {
        "id": ["1"],
        "name": ["A"],
        "source_file": ["first.csv"],
    }
    assert result.collect().to_dict(as_series=False) == {
        "id": ["1"],
        "name": ["A"],
        "source_file": ["first.csv"],
    }


def test_read_folder_csv_does_not_store_result_in_context_by_default(tmp_path):
    (tmp_path / "first.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )

    context = StepExecutionContext(extra_inputs={})

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
            },
        )
    )

    step.execute(context=context)

    assert context.extra_inputs == {}


def test_read_folder_csv_returns_existing_data_when_data_is_provided(tmp_path):
    (tmp_path / "first.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )

    existing_data = pl.DataFrame(
        {
            "existing": [100],
        }
    ).lazy()

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
            },
        )
    )

    result = step.execute(data=existing_data).collect()

    assert result.to_dict(as_series=False) == {
        "existing": [100],
    }


def test_read_folder_csv_still_reads_and_stores_when_existing_data_is_provided(tmp_path):
    (tmp_path / "first.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )

    existing_data = pl.DataFrame(
        {
            "existing": [100],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={})

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
                "context_store": True,
                "context_key": "folder_csv",
            },
        )
    )

    result = step.execute(data=existing_data, context=context).collect()

    assert result.to_dict(as_series=False) == {
        "existing": [100],
    }
    assert context.extra_inputs["folder_csv"].collect().to_dict(as_series=False) == {
        "id": ["1"],
        "name": ["A"],
        "source_file": ["first.csv"],
    }


def test_read_folder_csv_returns_lazyframe(tmp_path):
    (tmp_path / "first.csv").write_text(
        "id,name\n1,A\n",
        encoding="utf-8",
    )

    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
            },
        )
    )

    result = step.execute()

    assert isinstance(result, pl.LazyFrame)


def test_read_folder_csv_rejects_missing_path_parameter():
    with pytest.raises(ValidationError):
        ReadFolderCsvStep(
            StepConfig(
                key="read_folder_csv",
                parameters={},
            )
        )


def test_read_folder_csv_raises_when_no_matching_files(tmp_path):
    step = ReadFolderCsvStep(
        StepConfig(
            key="read_folder_csv",
            parameters={
                "path": tmp_path,
                "pattern": "*.csv",
            },
        )
    )

    with pytest.raises(FileNotFoundError):
        step.execute()
        
def test_read_folder_excel_reads_and_concatenates_excel_files(tmp_path):
    first_path = tmp_path / "first.xlsx"
    second_path = tmp_path / "second.xlsx"

    pd.DataFrame({"id": [1], "name": ["A"]}).to_excel(first_path, index=False)
    pd.DataFrame({"id": [2], "name": ["B"]}).to_excel(second_path, index=False)

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
            },
        )
    )

    result = step.execute().collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", "B"],
        "source_file": ["first.xlsx", "second.xlsx"],
    }


def test_read_folder_excel_uses_custom_pattern(tmp_path):
    keep_path = tmp_path / "keep.xlsx"
    skip_path = tmp_path / "skip.xlsm"

    pd.DataFrame({"id": [1]}).to_excel(keep_path, index=False)
    pd.DataFrame({"id": [2]}).to_excel(skip_path, index=False)

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
                "pattern": "*.xlsx",
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "source_file": ["keep.xlsx"],
    }


def test_read_folder_excel_reads_selected_sheet(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    with pd.ExcelWriter(excel_path) as writer:
        pd.DataFrame({"id": [1], "name": ["A"]}).to_excel(
            writer,
            sheet_name="first",
            index=False,
        )
        pd.DataFrame({"id": [2], "name": ["B"]}).to_excel(
            writer,
            sheet_name="second",
            index=False,
        )

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
                "sheet": "second",
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": [2],
        "name": ["B"],
        "source_file": ["input.xlsx"],
    }


def test_read_folder_excel_can_disable_source_file_column(tmp_path):
    first_path = tmp_path / "first.xlsx"
    second_path = tmp_path / "second.xlsx"

    pd.DataFrame({"id": [1]}).to_excel(first_path, index=False)
    pd.DataFrame({"id": [2]}).to_excel(second_path, index=False)

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
                "add_source_file": False,
            },
        )
    )

    result = step.execute().collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
    }


def test_read_folder_excel_uses_custom_source_column(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pd.DataFrame({"id": [1]}).to_excel(excel_path, index=False)

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
                "source_column": "file_name",
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "file_name": ["input.xlsx"],
    }


def test_read_folder_excel_can_add_source_path_column(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pd.DataFrame({"id": [1]}).to_excel(excel_path, index=False)

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
                "add_source_path": True,
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "source_file": ["input.xlsx"],
        "source_path": [str(excel_path)],
    }


def test_read_folder_excel_uses_custom_source_path_column(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pd.DataFrame({"id": [1]}).to_excel(excel_path, index=False)

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
                "add_source_path": True,
                "source_path_column": "file_path",
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "source_file": ["input.xlsx"],
        "file_path": [str(excel_path)],
    }


def test_read_folder_excel_supports_recursive_search(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()

    root_path = tmp_path / "root.xlsx"
    nested_path = nested / "nested.xlsx"

    pd.DataFrame({"id": [1]}).to_excel(root_path, index=False)
    pd.DataFrame({"id": [2]}).to_excel(nested_path, index=False)

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
                "recursive": True,
            },
        )
    )

    result = step.execute().collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "source_file": ["root.xlsx", "nested.xlsx"],
    }


def test_read_folder_excel_non_recursive_ignores_nested_files(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()

    root_path = tmp_path / "root.xlsx"
    nested_path = nested / "nested.xlsx"

    pd.DataFrame({"id": [1]}).to_excel(root_path, index=False)
    pd.DataFrame({"id": [2]}).to_excel(nested_path, index=False)

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
                "recursive": False,
            },
        )
    )

    result = step.execute().collect()

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "source_file": ["root.xlsx"],
    }


def test_read_folder_excel_stores_result_in_context_when_enabled(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pd.DataFrame({"id": [1], "name": ["A"]}).to_excel(excel_path, index=False)

    context = StepExecutionContext(extra_inputs={})

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
                "context_store": True,
                "context_key": "folder_excel",
            },
        )
    )

    result = step.execute(context=context)

    assert "folder_excel" in context.extra_inputs
    assert isinstance(context.extra_inputs["folder_excel"], pl.LazyFrame)
    assert context.extra_inputs["folder_excel"].collect().to_dict(as_series=False) == {
        "id": [1],
        "name": ["A"],
        "source_file": ["input.xlsx"],
    }
    assert result.collect().to_dict(as_series=False) == {
        "id": [1],
        "name": ["A"],
        "source_file": ["input.xlsx"],
    }


def test_read_folder_excel_does_not_store_result_in_context_by_default(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pd.DataFrame({"id": [1]}).to_excel(excel_path, index=False)

    context = StepExecutionContext(extra_inputs={})

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
            },
        )
    )

    step.execute(context=context)

    assert context.extra_inputs == {}


def test_read_folder_excel_returns_existing_data_when_data_is_provided(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pd.DataFrame({"id": [1]}).to_excel(excel_path, index=False)

    existing_data = pl.DataFrame(
        {
            "existing": [100],
        }
    ).lazy()

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
            },
        )
    )

    result = step.execute(data=existing_data).collect()

    assert result.to_dict(as_series=False) == {
        "existing": [100],
    }


def test_read_folder_excel_still_reads_and_stores_when_existing_data_is_provided(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pd.DataFrame({"id": [1], "name": ["A"]}).to_excel(excel_path, index=False)

    existing_data = pl.DataFrame(
        {
            "existing": [100],
        }
    ).lazy()

    context = StepExecutionContext(extra_inputs={})

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
                "context_store": True,
                "context_key": "folder_excel",
            },
        )
    )

    result = step.execute(data=existing_data, context=context).collect()

    assert result.to_dict(as_series=False) == {
        "existing": [100],
    }
    assert context.extra_inputs["folder_excel"].collect().to_dict(as_series=False) == {
        "id": [1],
        "name": ["A"],
        "source_file": ["input.xlsx"],
    }


def test_read_folder_excel_returns_lazyframe(tmp_path):
    excel_path = tmp_path / "input.xlsx"

    pd.DataFrame({"id": [1]}).to_excel(excel_path, index=False)

    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
            },
        )
    )

    result = step.execute()

    assert isinstance(result, pl.LazyFrame)


def test_read_folder_excel_rejects_missing_path_parameter():
    with pytest.raises(ValidationError):
        ReadFolderExcelStep(
            StepConfig(
                key="read_folder_excel",
                parameters={},
            )
        )


def test_read_folder_excel_raises_when_no_matching_files(tmp_path):
    step = ReadFolderExcelStep(
        StepConfig(
            key="read_folder_excel",
            parameters={
                "path": tmp_path,
                "pattern": "*.xlsx",
            },
        )
    )

    with pytest.raises(FileNotFoundError):
        step.execute()
        
def test_regex_extract_creates_output_column_from_first_group():
    df = pl.DataFrame(
        {
            "text": ["APM-123", "APM-456", "NO_MATCH"],
        }
    ).lazy()

    step = RegexExtractStep(
        StepConfig(
            key="regex_extract",
            parameters={
                "column": "text",
                "pattern": r"APM-(\d+)",
                "output_column": "number",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "text": ["APM-123", "APM-456", "NO_MATCH"],
        "number": ["123", "456", None],
    }


def test_regex_extract_supports_custom_group_index():
    df = pl.DataFrame(
        {
            "text": ["APM-123-PL", "APM-456-DE"],
        }
    ).lazy()

    step = RegexExtractStep(
        StepConfig(
            key="regex_extract",
            parameters={
                "column": "text",
                "pattern": r"APM-(\d+)-([A-Z]{2})",
                "output_column": "country",
                "group_index": 2,
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "text": ["APM-123-PL", "APM-456-DE"],
        "country": ["PL", "DE"],
    }


def test_regex_extract_can_overwrite_existing_column():
    df = pl.DataFrame(
        {
            "text": ["APM-123", "APM-456"],
            "number": ["old", "old"],
        }
    ).lazy()

    step = RegexExtractStep(
        StepConfig(
            key="regex_extract",
            parameters={
                "column": "text",
                "pattern": r"APM-(\d+)",
                "output_column": "number",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "text": ["APM-123", "APM-456"],
        "number": ["123", "456"],
    }


def test_regex_extract_returns_lazyframe():
    df = pl.DataFrame({"text": ["APM-123"]}).lazy()

    step = RegexExtractStep(
        StepConfig(
            key="regex_extract",
            parameters={
                "column": "text",
                "pattern": r"APM-(\d+)",
                "output_column": "number",
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_regex_extract_rejects_missing_column_parameter():
    with pytest.raises(ValidationError):
        RegexExtractStep(
            StepConfig(
                key="regex_extract",
                parameters={
                    "pattern": r"APM-(\d+)",
                    "output_column": "number",
                },
            )
        )


def test_regex_extract_rejects_missing_pattern_parameter():
    with pytest.raises(ValidationError):
        RegexExtractStep(
            StepConfig(
                key="regex_extract",
                parameters={
                    "column": "text",
                    "output_column": "number",
                },
            )
        )


def test_regex_extract_rejects_missing_output_column_parameter():
    with pytest.raises(ValidationError):
        RegexExtractStep(
            StepConfig(
                key="regex_extract",
                parameters={
                    "column": "text",
                    "pattern": r"APM-(\d+)",
                },
            )
        )


def test_regex_extract_raises_for_missing_dataframe_column():
    df = pl.DataFrame({"text": ["APM-123"]}).lazy()

    step = RegexExtractStep(
        StepConfig(
            key="regex_extract",
            parameters={
                "column": "missing",
                "pattern": r"APM-(\d+)",
                "output_column": "number",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_regex_extract_raises_for_invalid_regex_pattern():
    df = pl.DataFrame({"text": ["APM-123"]}).lazy()

    step = RegexExtractStep(
        StepConfig(
            key="regex_extract",
            parameters={
                "column": "text",
                "pattern": r"APM-(\d+",
                "output_column": "number",
            },
        )
    )

    with pytest.raises(pl.exceptions.ComputeError):
        step.execute(df).collect()
        
def test_remove_duplicates_removes_duplicate_rows_using_all_columns():
    df = pl.DataFrame(
        {
            "id": [1, 1, 2],
            "name": ["A", "A", "B"],
        }
    ).lazy()

    step = RemoveDuplicatesStep(
        StepConfig(
            key="remove_duplicates",
            parameters={},
        )
    )

    result = step.execute(df).collect().sort("id")

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", "B"],
    }


def test_remove_duplicates_uses_subset_columns():
    df = pl.DataFrame(
        {
            "id": [1, 1, 2],
            "name": ["A", "B", "C"],
        }
    ).lazy()

    step = RemoveDuplicatesStep(
        StepConfig(
            key="remove_duplicates",
            parameters={
                "columns": ["id"],
            },
        )
    )

    result = step.execute(df).collect().sort("id")

    assert result.height == 2
    assert result["id"].to_list() == [1, 2]


def test_remove_duplicates_keep_first():
    df = pl.DataFrame(
        {
            "id": [1, 1],
            "name": ["first", "second"],
        }
    ).lazy()

    step = RemoveDuplicatesStep(
        StepConfig(
            key="remove_duplicates",
            parameters={
                "columns": ["id"],
                "keep": "first",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "name": ["first"],
    }


def test_remove_duplicates_keep_last():
    df = pl.DataFrame(
        {
            "id": [1, 1],
            "name": ["first", "second"],
        }
    ).lazy()

    step = RemoveDuplicatesStep(
        StepConfig(
            key="remove_duplicates",
            parameters={
                "columns": ["id"],
                "keep": "last",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "name": ["second"],
    }


def test_remove_duplicates_keeps_all_rows_when_no_duplicates_exist():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
        }
    ).lazy()

    step = RemoveDuplicatesStep(
        StepConfig(
            key="remove_duplicates",
            parameters={},
        )
    )

    result = step.execute(df).collect().sort("id")

    assert result["id"].to_list() == [1, 2, 3]


def test_remove_duplicates_returns_lazyframe():
    df = pl.DataFrame(
        {
            "id": [1, 1],
        }
    ).lazy()

    step = RemoveDuplicatesStep(
        StepConfig(
            key="remove_duplicates",
            parameters={},
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_remove_duplicates_rejects_invalid_keep_value():
    with pytest.raises(ValidationError):
        RemoveDuplicatesStep(
            StepConfig(
                key="remove_duplicates",
                parameters={
                    "keep": "any",
                },
            )
        )


def test_remove_duplicates_raises_for_missing_subset_column():
    df = pl.DataFrame(
        {
            "id": [1, 1],
        }
    ).lazy()

    step = RemoveDuplicatesStep(
        StepConfig(
            key="remove_duplicates",
            parameters={
                "columns": ["missing"],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_rename_columns_renames_single_column():
    df = pl.DataFrame(
        {
            "old_name": [1, 2],
        }
    ).lazy()

    step = RenameColumnsStep(
        StepConfig(
            key="rename_columns",
            parameters={
                "mapping": {"old_name": "new_name"},
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "new_name": [1, 2],
    }


def test_rename_columns_renames_multiple_columns():
    df = pl.DataFrame(
        {
            "old_id": [1, 2],
            "old_name": ["A", "B"],
            "unchanged": [10, 20],
        }
    ).lazy()

    step = RenameColumnsStep(
        StepConfig(
            key="rename_columns",
            parameters={
                "mapping": {
                    "old_id": "id",
                    "old_name": "name",
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", "B"],
        "unchanged": [10, 20],
    }


def test_rename_columns_preserves_column_order():
    df = pl.DataFrame(
        {
            "a": [1],
            "b": [2],
            "c": [3],
        }
    ).lazy()

    step = RenameColumnsStep(
        StepConfig(
            key="rename_columns",
            parameters={
                "mapping": {
                    "b": "renamed_b",
                    "c": "renamed_c",
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result.columns == ["a", "renamed_b", "renamed_c"]


def test_rename_columns_returns_lazyframe():
    df = pl.DataFrame(
        {
            "old_name": [1],
        }
    ).lazy()

    step = RenameColumnsStep(
        StepConfig(
            key="rename_columns",
            parameters={
                "mapping": {"old_name": "new_name"},
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_rename_columns_rejects_missing_mapping_parameter():
    with pytest.raises(ValidationError):
        RenameColumnsStep(
            StepConfig(
                key="rename_columns",
                parameters={},
            )
        )


def test_rename_columns_raises_for_missing_dataframe_column():
    df = pl.DataFrame(
        {
            "existing": [1],
        }
    ).lazy()

    step = RenameColumnsStep(
        StepConfig(
            key="rename_columns",
            parameters={
                "mapping": {"missing": "new_name"},
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_rename_columns_raises_when_target_column_already_exists():
    df = pl.DataFrame(
        {
            "a": [1],
            "b": [2],
        }
    ).lazy()

    step = RenameColumnsStep(
        StepConfig(
            key="rename_columns",
            parameters={
                "mapping": {"a": "b"},
            },
        )
    )

    with pytest.raises(pl.exceptions.DuplicateError):
        step.execute(df).collect()
        
def test_reorder_columns_reorders_columns():
    df = pl.DataFrame(
        {
            "a": [1],
            "b": [2],
            "c": [3],
        }
    ).lazy()

    step = ReorderColumnsStep(
        StepConfig(
            key="reorder_columns",
            parameters={
                "columns": ["c", "a", "b"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.columns == ["c", "a", "b"]
    assert result.to_dict(as_series=False) == {
        "c": [3],
        "a": [1],
        "b": [2],
    }


def test_reorder_columns_can_select_subset_of_columns():
    df = pl.DataFrame(
        {
            "a": [1],
            "b": [2],
            "c": [3],
        }
    ).lazy()

    step = ReorderColumnsStep(
        StepConfig(
            key="reorder_columns",
            parameters={
                "columns": ["b", "a"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "b": [2],
        "a": [1],
    }


def test_reorder_columns_keeps_order_when_same_order_is_given():
    df = pl.DataFrame(
        {
            "a": [1],
            "b": [2],
        }
    ).lazy()

    step = ReorderColumnsStep(
        StepConfig(
            key="reorder_columns",
            parameters={
                "columns": ["a", "b"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.columns == ["a", "b"]


def test_reorder_columns_returns_lazyframe():
    df = pl.DataFrame(
        {
            "a": [1],
            "b": [2],
        }
    ).lazy()

    step = ReorderColumnsStep(
        StepConfig(
            key="reorder_columns",
            parameters={
                "columns": ["b", "a"],
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_reorder_columns_rejects_missing_columns_parameter():
    with pytest.raises(ValidationError):
        ReorderColumnsStep(
            StepConfig(
                key="reorder_columns",
                parameters={},
            )
        )


def test_reorder_columns_raises_for_missing_dataframe_column():
    df = pl.DataFrame(
        {
            "a": [1],
        }
    ).lazy()

    step = ReorderColumnsStep(
        StepConfig(
            key="reorder_columns",
            parameters={
                "columns": ["a", "missing"],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_replace_values_replaces_single_value_pair():
    df = pl.DataFrame(
        {
            "status": ["ok", "nok", "ok"],
        }
    ).lazy()

    step = ReplaceValuesStep(
        StepConfig(
            key="replace_values",
            parameters={
                "column": "status",
                "old": "nok",
                "new": "fail",
            },
        )
    )

    result = step.execute(df).collect()

    assert result["status"].to_list() == ["ok", "fail", "ok"]


def test_replace_values_replaces_multiple_values_using_mapping():
    df = pl.DataFrame(
        {
            "status": ["ok", "nok", "unknown", "ok"],
        }
    ).lazy()

    step = ReplaceValuesStep(
        StepConfig(
            key="replace_values",
            parameters={
                "column": "status",
                "mapping": {
                    "ok": "success",
                    "nok": "fail",
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result["status"].to_list() == [
        "success",
        "fail",
        "unknown",
        "success",
    ]


def test_replace_values_preserves_unmatched_values():
    df = pl.DataFrame(
        {
            "value": [1, 2, 3],
        }
    ).lazy()

    step = ReplaceValuesStep(
        StepConfig(
            key="replace_values",
            parameters={
                "column": "value",
                "old": 2,
                "new": 20,
            },
        )
    )

    result = step.execute(df).collect()

    assert result["value"].to_list() == [1, 20, 3]


def test_replace_values_does_not_modify_other_columns():
    df = pl.DataFrame(
        {
            "status": ["ok", "nok"],
            "id": [1, 2],
        }
    ).lazy()

    step = ReplaceValuesStep(
        StepConfig(
            key="replace_values",
            parameters={
                "column": "status",
                "old": "nok",
                "new": "fail",
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "status": ["ok", "fail"],
        "id": [1, 2],
    }


def test_replace_values_can_replace_with_null():
    df = pl.DataFrame(
        {
            "status": ["ok", "unknown", "nok"],
        }
    ).lazy()

    step = ReplaceValuesStep(
        StepConfig(
            key="replace_values",
            parameters={
                "column": "status",
                "old": "unknown",
                "new": None,
            },
        )
    )

    result = step.execute(df).collect()

    assert result["status"].to_list() == ["ok", None, "nok"]


def test_replace_values_mapping_can_replace_with_null():
    df = pl.DataFrame(
        {
            "status": ["ok", "unknown", "nok"],
        }
    ).lazy()

    step = ReplaceValuesStep(
        StepConfig(
            key="replace_values",
            parameters={
                "column": "status",
                "mapping": {
                    "unknown": None,
                },
            },
        )
    )

    result = step.execute(df).collect()

    assert result["status"].to_list() == ["ok", None, "nok"]


def test_replace_values_returns_lazyframe():
    df = pl.DataFrame(
        {
            "status": ["ok", "nok"],
        }
    ).lazy()

    step = ReplaceValuesStep(
        StepConfig(
            key="replace_values",
            parameters={
                "column": "status",
                "old": "nok",
                "new": "fail",
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_replace_values_rejects_missing_column_parameter():
    with pytest.raises(ValidationError):
        ReplaceValuesStep(
            StepConfig(
                key="replace_values",
                parameters={
                    "old": "nok",
                    "new": "fail",
                },
            )
        )


def test_replace_values_rejects_missing_pair_and_mapping():
    with pytest.raises(ValidationError):
        ReplaceValuesStep(
            StepConfig(
                key="replace_values",
                parameters={
                    "column": "status",
                },
            )
        )


def test_replace_values_rejects_pair_and_mapping_together():
    with pytest.raises(ValidationError):
        ReplaceValuesStep(
            StepConfig(
                key="replace_values",
                parameters={
                    "column": "status",
                    "old": "nok",
                    "new": "fail",
                    "mapping": {
                        "ok": "success",
                    },
                },
            )
        )


def test_replace_values_raises_for_missing_dataframe_column():
    df = pl.DataFrame(
        {
            "status": ["ok"],
        }
    ).lazy()

    step = ReplaceValuesStep(
        StepConfig(
            key="replace_values",
            parameters={
                "column": "missing",
                "old": "ok",
                "new": "success",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_select_columns_selects_requested_columns():
    df = pl.DataFrame(
        {
            "id": [1, 2],
            "name": ["A", "B"],
            "value": [10, 20],
        }
    ).lazy()

    step = SelectColumnsStep(
        StepConfig(
            key="select_columns",
            parameters={
                "columns": ["name", "value"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "name": ["A", "B"],
        "value": [10, 20],
    }


def test_select_columns_preserves_requested_order():
    df = pl.DataFrame(
        {
            "id": [1],
            "name": ["A"],
            "value": [10],
        }
    ).lazy()

    step = SelectColumnsStep(
        StepConfig(
            key="select_columns",
            parameters={
                "columns": ["value", "id"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.columns == ["value", "id"]


def test_select_columns_can_select_single_column():
    df = pl.DataFrame(
        {
            "id": [1, 2],
            "name": ["A", "B"],
        }
    ).lazy()

    step = SelectColumnsStep(
        StepConfig(
            key="select_columns",
            parameters={
                "columns": ["id"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
    }


def test_select_columns_returns_lazyframe():
    df = pl.DataFrame(
        {
            "id": [1],
            "name": ["A"],
        }
    ).lazy()

    step = SelectColumnsStep(
        StepConfig(
            key="select_columns",
            parameters={
                "columns": ["id"],
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_select_columns_rejects_missing_columns_parameter():
    with pytest.raises(ValidationError):
        SelectColumnsStep(
            StepConfig(
                key="select_columns",
                parameters={},
            )
        )


def test_select_columns_raises_for_missing_dataframe_column():
    df = pl.DataFrame(
        {
            "id": [1],
        }
    ).lazy()

    step = SelectColumnsStep(
        StepConfig(
            key="select_columns",
            parameters={
                "columns": ["id", "missing"],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_sort_rows_sorts_by_single_column_ascending():
    df = pl.DataFrame(
        {
            "id": [3, 1, 2],
            "name": ["C", "A", "B"],
        }
    ).lazy()

    step = SortRowsStep(
        StepConfig(
            key="sort_rows",
            parameters={
                "columns": [{"name": "id", "direction": "asc"}],
            },
        )
    )

    result = step.execute(df).collect()

    assert result["id"].to_list() == [1, 2, 3]


def test_sort_rows_sorts_by_single_column_descending():
    df = pl.DataFrame(
        {
            "id": [3, 1, 2],
        }
    ).lazy()

    step = SortRowsStep(
        StepConfig(
            key="sort_rows",
            parameters={
                "columns": [{"name": "id", "direction": "desc"}],
            },
        )
    )

    result = step.execute(df).collect()

    assert result["id"].to_list() == [3, 2, 1]


def test_sort_rows_uses_ascending_by_default():
    df = pl.DataFrame(
        {
            "id": [3, 1, 2],
        }
    ).lazy()

    step = SortRowsStep(
        StepConfig(
            key="sort_rows",
            parameters={
                "columns": [{"name": "id"}],
            },
        )
    )

    result = step.execute(df).collect()

    assert result["id"].to_list() == [1, 2, 3]


def test_sort_rows_sorts_by_multiple_columns_with_different_directions():
    df = pl.DataFrame(
        {
            "country": ["PL", "PL", "DE", "DE"],
            "value": [10, 30, 20, 5],
        }
    ).lazy()

    step = SortRowsStep(
        StepConfig(
            key="sort_rows",
            parameters={
                "columns": [
                    {"name": "country", "direction": "asc"},
                    {"name": "value", "direction": "desc"},
                ],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "country": ["DE", "DE", "PL", "PL"],
        "value": [20, 5, 30, 10],
    }


def test_sort_rows_does_not_modify_columns():
    df = pl.DataFrame(
        {
            "id": [2, 1],
            "name": ["B", "A"],
        }
    ).lazy()

    step = SortRowsStep(
        StepConfig(
            key="sort_rows",
            parameters={
                "columns": [{"name": "id"}],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.columns == ["id", "name"]
    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", "B"],
    }


def test_sort_rows_returns_lazyframe():
    df = pl.DataFrame(
        {
            "id": [2, 1],
        }
    ).lazy()

    step = SortRowsStep(
        StepConfig(
            key="sort_rows",
            parameters={
                "columns": [{"name": "id"}],
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_sort_rows_rejects_missing_columns_parameter():
    with pytest.raises(ValidationError):
        SortRowsStep(
            StepConfig(
                key="sort_rows",
                parameters={},
            )
        )


def test_sort_rows_rejects_missing_column_name():
    with pytest.raises(ValidationError):
        SortRowsStep(
            StepConfig(
                key="sort_rows",
                parameters={
                    "columns": [{"direction": "asc"}],
                },
            )
        )


def test_sort_rows_rejects_invalid_direction():
    with pytest.raises(ValidationError):
        SortRowsStep(
            StepConfig(
                key="sort_rows",
                parameters={
                    "columns": [{"name": "id", "direction": "ascending"}],
                },
            )
        )


def test_sort_rows_raises_for_missing_dataframe_column():
    df = pl.DataFrame(
        {
            "id": [1],
        }
    ).lazy()

    step = SortRowsStep(
        StepConfig(
            key="sort_rows",
            parameters={
                "columns": [{"name": "missing"}],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_split_column_splits_text_column_into_multiple_columns():
    df = pl.DataFrame(
        {
            "full_name": ["John Smith", "Anna Nowak"],
        }
    ).lazy()

    step = SplitColumnStep(
        StepConfig(
            key="split_column",
            parameters={
                "column": "full_name",
                "delimiter": " ",
                "into": ["first_name", "last_name"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "full_name": ["John Smith", "Anna Nowak"],
        "first_name": ["John", "Anna"],
        "last_name": ["Smith", "Nowak"],
    }


def test_split_column_drops_original_column_when_enabled():
    df = pl.DataFrame(
        {
            "code": ["APM-123-PL"],
        }
    ).lazy()

    step = SplitColumnStep(
        StepConfig(
            key="split_column",
            parameters={
                "column": "code",
                "delimiter": "-",
                "into": ["prefix", "number", "country"],
                "drop_original": True,
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "prefix": ["APM"],
        "number": ["123"],
        "country": ["PL"],
    }


def test_split_column_fills_missing_parts_with_null():
    df = pl.DataFrame(
        {
            "code": ["APM-123", "BOX"],
        }
    ).lazy()

    step = SplitColumnStep(
        StepConfig(
            key="split_column",
            parameters={
                "column": "code",
                "delimiter": "-",
                "into": ["prefix", "number", "country"],
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "code": ["APM-123", "BOX"],
        "prefix": ["APM", "BOX"],
        "number": ["123", None],
        "country": [None, None],
    }


def test_split_column_respects_max_splits():
    df = pl.DataFrame(
        {
            "code": ["A-B-C-D"],
        }
    ).lazy()

    step = SplitColumnStep(
        StepConfig(
            key="split_column",
            parameters={
                "column": "code",
                "delimiter": "-",
                "into": ["first", "second"],
                "max_splits": 1,
            },
        )
    )

    result = step.execute(df).collect()

    assert result.to_dict(as_series=False) == {
        "code": ["A-B-C-D"],
        "first": ["A"],
        "second": ["B"],
    }


def test_split_column_returns_lazyframe():
    df = pl.DataFrame(
        {
            "code": ["A-B"],
        }
    ).lazy()

    step = SplitColumnStep(
        StepConfig(
            key="split_column",
            parameters={
                "column": "code",
                "delimiter": "-",
                "into": ["a", "b"],
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_split_column_rejects_missing_column_parameter():
    with pytest.raises(ValidationError):
        SplitColumnStep(
            StepConfig(
                key="split_column",
                parameters={
                    "delimiter": "-",
                    "into": ["a", "b"],
                },
            )
        )


def test_split_column_rejects_missing_delimiter_parameter():
    with pytest.raises(ValidationError):
        SplitColumnStep(
            StepConfig(
                key="split_column",
                parameters={
                    "column": "code",
                    "into": ["a", "b"],
                },
            )
        )


def test_split_column_rejects_missing_into_parameter():
    with pytest.raises(ValidationError):
        SplitColumnStep(
            StepConfig(
                key="split_column",
                parameters={
                    "column": "code",
                    "delimiter": "-",
                },
            )
        )


def test_split_column_raises_for_missing_dataframe_column():
    df = pl.DataFrame(
        {
            "code": ["A-B"],
        }
    ).lazy()

    step = SplitColumnStep(
        StepConfig(
            key="split_column",
            parameters={
                "column": "missing",
                "delimiter": "-",
                "into": ["a", "b"],
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_unpivot_converts_wide_columns_to_long_rows():
    df = pl.DataFrame(
        {
            "id": [1, 2],
            "height": [180, 170],
            "weight": [80, 70],
        }
    ).lazy()

    step = UnpivotStep(
        StepConfig(
            key="unpivot",
            parameters={
                "on": ["height", "weight"],
                "index": ["id"],
                "variable_name": "metric",
                "value_name": "value",
            },
        )
    )

    result = step.execute(df).collect().sort(["id", "metric"])

    assert result.to_dict(as_series=False) == {
        "id": [1, 1, 2, 2],
        "metric": ["height", "weight", "height", "weight"],
        "value": [180, 80, 170, 70],
    }


def test_unpivot_supports_multiple_index_columns():
    df = pl.DataFrame(
        {
            "country": ["PL", "DE"],
            "id": [1, 2],
            "height": [180, 170],
            "weight": [80, 70],
        }
    ).lazy()

    step = UnpivotStep(
        StepConfig(
            key="unpivot",
            parameters={
                "on": ["height", "weight"],
                "index": ["country", "id"],
                "variable_name": "metric",
                "value_name": "value",
            },
        )
    )

    result = step.execute(df).collect().sort(["country", "id", "metric"])

    assert result.to_dict(as_series=False) == {
        "country": ["DE", "DE", "PL", "PL"],
        "id": [2, 2, 1, 1],
        "metric": ["height", "weight", "height", "weight"],
        "value": [170, 70, 180, 80],
    }


def test_unpivot_uses_custom_variable_and_value_names():
    df = pl.DataFrame(
        {
            "id": [1],
            "t1": [10],
            "t2": [20],
        }
    ).lazy()

    step = UnpivotStep(
        StepConfig(
            key="unpivot",
            parameters={
                "on": ["t1", "t2"],
                "index": ["id"],
                "variable_name": "sensor",
                "value_name": "temperature",
            },
        )
    )

    result = step.execute(df).collect().sort("sensor")

    assert result.to_dict(as_series=False) == {
        "id": [1, 1],
        "sensor": ["t1", "t2"],
        "temperature": [10, 20],
    }


def test_unpivot_returns_lazyframe():
    df = pl.DataFrame(
        {
            "id": [1],
            "height": [180],
        }
    ).lazy()

    step = UnpivotStep(
        StepConfig(
            key="unpivot",
            parameters={
                "on": ["height"],
                "index": ["id"],
                "variable_name": "metric",
                "value_name": "value",
            },
        )
    )

    result = step.execute(df)

    assert isinstance(result, pl.LazyFrame)


def test_unpivot_rejects_missing_on_parameter():
    with pytest.raises(ValidationError):
        UnpivotStep(
            StepConfig(
                key="unpivot",
                parameters={
                    "index": ["id"],
                    "variable_name": "metric",
                    "value_name": "value",
                },
            )
        )


def test_unpivot_rejects_missing_index_parameter():
    with pytest.raises(ValidationError):
        UnpivotStep(
            StepConfig(
                key="unpivot",
                parameters={
                    "on": ["height"],
                    "variable_name": "metric",
                    "value_name": "value",
                },
            )
        )


def test_unpivot_rejects_missing_variable_name_parameter():
    with pytest.raises(ValidationError):
        UnpivotStep(
            StepConfig(
                key="unpivot",
                parameters={
                    "on": ["height"],
                    "index": ["id"],
                    "value_name": "value",
                },
            )
        )


def test_unpivot_rejects_missing_value_name_parameter():
    with pytest.raises(ValidationError):
        UnpivotStep(
            StepConfig(
                key="unpivot",
                parameters={
                    "on": ["height"],
                    "index": ["id"],
                    "variable_name": "metric",
                },
            )
        )


def test_unpivot_raises_for_missing_on_column():
    df = pl.DataFrame(
        {
            "id": [1],
            "height": [180],
        }
    ).lazy()

    step = UnpivotStep(
        StepConfig(
            key="unpivot",
            parameters={
                "on": ["missing"],
                "index": ["id"],
                "variable_name": "metric",
                "value_name": "value",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()


def test_unpivot_raises_for_missing_index_column():
    df = pl.DataFrame(
        {
            "id": [1],
            "height": [180],
        }
    ).lazy()

    step = UnpivotStep(
        StepConfig(
            key="unpivot",
            parameters={
                "on": ["height"],
                "index": ["missing"],
                "variable_name": "metric",
                "value_name": "value",
            },
        )
    )

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        step.execute(df).collect()
        
def test_write_csv_writes_dataframe_to_file(tmp_path):
    output_path = tmp_path / "output.csv"

    df = pl.DataFrame(
        {
            "id": [1, 2],
            "name": ["A", "B"],
        }
    ).lazy()

    step = WriteCsvStep(
        StepConfig(
            key="write_csv",
            parameters={
                "path": output_path,
            },
        )
    )

    step.execute(df)

    result = pl.read_csv(output_path)

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", "B"],
    }


def test_write_csv_uses_custom_separator(tmp_path):
    output_path = tmp_path / "output.csv"

    df = pl.DataFrame(
        {
            "id": [1],
            "name": ["A"],
        }
    ).lazy()

    step = WriteCsvStep(
        StepConfig(
            key="write_csv",
            parameters={
                "path": output_path,
                "separator": ";",
            },
        )
    )

    step.execute(df)

    result = pl.read_csv(
        output_path,
        separator=";",
    )

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "name": ["A"],
    }


def test_write_csv_returns_original_lazyframe():
    output_path = Path("dummy.csv")

    df = pl.DataFrame(
        {
            "id": [1],
        }
    ).lazy()

    step = WriteCsvStep(
        StepConfig(
            key="write_csv",
            parameters={
                "path": output_path,
            },
        )
    )

    result = step.execute(df)

    assert result is df


def test_write_csv_creates_file_when_output_directory_exists(tmp_path):
    output_path = tmp_path / "result.csv"

    df = pl.DataFrame(
        {
            "value": [123],
        }
    ).lazy()

    step = WriteCsvStep(
        StepConfig(
            key="write_csv",
            parameters={
                "path": output_path,
            },
        )
    )

    step.execute(df)

    assert output_path.exists()
    assert output_path.is_file()


def test_write_csv_rejects_missing_path_parameter():
    with pytest.raises(ValidationError):
        WriteCsvStep(
            StepConfig(
                key="write_csv",
                parameters={},
            )
        )


def test_write_csv_raises_when_data_is_none(tmp_path):
    output_path = tmp_path / "output.csv"

    step = WriteCsvStep(
        StepConfig(
            key="write_csv",
            parameters={
                "path": output_path,
            },
        )
    )

    with pytest.raises(Exception):
        step.execute(None)
        
def test_write_excel_writes_dataframe_to_file(tmp_path):
    output_path = tmp_path / "output.xlsx"

    df = pl.DataFrame(
        {
            "id": [1, 2],
            "name": ["A", "B"],
        }
    ).lazy()

    step = WriteExcelStep(
        StepConfig(
            key="write_excel",
            parameters={
                "path": output_path,
            },
        )
    )

    step.execute(df)

    result = pl.read_excel(output_path)

    assert result.to_dict(as_series=False) == {
        "id": [1, 2],
        "name": ["A", "B"],
    }


def test_write_excel_writes_selected_sheet(tmp_path):
    output_path = tmp_path / "output.xlsx"

    df = pl.DataFrame(
        {
            "id": [1],
            "name": ["A"],
        }
    ).lazy()

    step = WriteExcelStep(
        StepConfig(
            key="write_excel",
            parameters={
                "path": output_path,
                "sheet": "data",
            },
        )
    )

    step.execute(df)

    result = pl.read_excel(
        output_path,
        sheet_name="data",
    )

    assert result.to_dict(as_series=False) == {
        "id": [1],
        "name": ["A"],
    }


def test_write_excel_returns_original_lazyframe(tmp_path):
    output_path = tmp_path / "output.xlsx"

    df = pl.DataFrame(
        {
            "id": [1],
        }
    ).lazy()

    step = WriteExcelStep(
        StepConfig(
            key="write_excel",
            parameters={
                "path": output_path,
            },
        )
    )

    result = step.execute(df)

    assert result is df


def test_write_excel_creates_file_when_output_directory_exists(tmp_path):
    output_path = tmp_path / "result.xlsx"

    df = pl.DataFrame(
        {
            "value": [123],
        }
    ).lazy()

    step = WriteExcelStep(
        StepConfig(
            key="write_excel",
            parameters={
                "path": output_path,
            },
        )
    )

    step.execute(df)

    assert output_path.exists()
    assert output_path.is_file()


def test_write_excel_rejects_missing_path_parameter():
    with pytest.raises(ValidationError):
        WriteExcelStep(
            StepConfig(
                key="write_excel",
                parameters={},
            )
        )


def test_write_excel_raises_when_data_is_none(tmp_path):
    output_path = tmp_path / "output.xlsx"

    step = WriteExcelStep(
        StepConfig(
            key="write_excel",
            parameters={
                "path": output_path,
            },
        )
    )

    with pytest.raises(Exception):
        step.execute(None)
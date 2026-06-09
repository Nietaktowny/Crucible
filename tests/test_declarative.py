import pytest
import polars as pl
from pydantic import ValidationError

from crucible.declarative.conditions import ConditionBuilder
from crucible.declarative.conditions.models import (
    AndCondition,
    ComparisonCondition,
    NotCondition,
    OrCondition,
)
from crucible.declarative.expressions import ExpressionBuilder
from crucible.declarative.expressions.models import (
    ColumnExpression,
    OperationExpression,
    ValueExpression,
)


def evaluate_expression(expression, df: pl.DataFrame | None = None, alias: str = "result"):
    df = df if df is not None else pl.DataFrame({"dummy": [1]})
    result = df.lazy().select(ExpressionBuilder().build(expression).alias(alias)).collect()
    return result[alias].to_list()


def filter_with_condition(condition, df: pl.DataFrame) -> pl.DataFrame:
    return df.lazy().filter(ConditionBuilder().build(condition)).collect()


def col(name: str) -> ColumnExpression:
    return ColumnExpression(column=name)


def val(value) -> ValueExpression:
    return ValueExpression(value=value)


def op(name: str, *args) -> OperationExpression:
    return OperationExpression(op=name, args=list(args))


def test_column_expression_selects_column() -> None:
    df = pl.DataFrame({"a": [1, 2, 3]})

    result = evaluate_expression(col("a"), df)

    assert result == [1, 2, 3]


def test_value_expression_creates_literal() -> None:
    result = evaluate_expression(val("abc"))

    assert result == ["abc"]


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        (op("add", col("a"), col("b")), [11, 22, 33]),
        (op("subtract", col("b"), col("a")), [9, 18, 27]),
        (op("multiply", col("a"), col("b")), [10, 40, 90]),
        (op("divide", col("b"), col("a")), [10.0, 10.0, 10.0]),
        (op("abs", col("negative")), [1, 2, 3]),
    ],
)
def test_numeric_operations(expression, expected) -> None:
    df = pl.DataFrame(
        {
            "a": [1, 2, 3],
            "b": [10, 20, 30],
            "negative": [-1, -2, -3],
        }
    )

    result = evaluate_expression(expression, df)

    assert result == expected


def test_safe_divide_returns_null_for_zero_or_null_denominator() -> None:
    df = pl.DataFrame(
        {
            "a": [10, 20, 30, 40],
            "b": [2, 0, None, 5],
        }
    )

    result = evaluate_expression(
        op("safe_divide", col("a"), col("b")),
        df,
    )

    assert result == [5.0, None, None, 8.0]


def test_round_operation() -> None:
    df = pl.DataFrame({"a": [1.234, 5.678]})

    result = evaluate_expression(
        op("round", col("a"), val(1)),
        df,
    )

    assert result == [1.2, 5.7]


def test_concat_operation() -> None:
    df = pl.DataFrame(
        {
            "first": ["A", "B"],
            "second": ["1", "2"],
        }
    )

    result = evaluate_expression(
        op("concat", col("first"), val("-"), col("second")),
        df,
    )

    assert result == ["A-1", "B-2"]


def test_coalesce_operation() -> None:
    df = pl.DataFrame(
        {
            "a": [None, "x", None],
            "b": ["fallback", "y", None],
            "c": ["last", "z", "final"],
        }
    )

    result = evaluate_expression(
        op("coalesce", col("a"), col("b"), col("c")),
        df,
    )

    assert result == ["fallback", "x", "final"]


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        (op("upper", col("text")), [" ABC ", " XYZ "]),
        (op("lower", col("text")), [" abc ", " xyz "]),
        (op("trim", col("text")), ["AbC", "xYz"]),
    ],
)
def test_string_operations(expression, expected) -> None:
    df = pl.DataFrame({"text": [" AbC ", " xYz "]})

    result = evaluate_expression(expression, df)

    assert result == expected


def test_nested_operation_expression() -> None:
    df = pl.DataFrame(
        {
            "a": [1, 2],
            "b": [10, 20],
            "c": [100, 200],
        }
    )

    expression = op(
        "multiply",
        op("add", col("a"), col("b")),
        col("c"),
    )

    result = evaluate_expression(expression, df)

    assert result == [1100, 4400]


@pytest.mark.parametrize(
    ("expression", "message"),
    [
        (op("add", col("a")), "requires 2 arguments"),
        (op("subtract", col("a")), "requires 2 arguments"),
        (op("multiply", col("a")), "requires 2 arguments"),
        (op("divide", col("a")), "requires 2 arguments"),
        (op("safe_divide", col("a")), "requires 2 arguments"),
        (op("round", col("a")), "requires 2 arguments"),
        (op("abs", col("a"), col("b")), "requires 1 arguments"),
        (op("concat"), "requires at least 1"),
        (op("coalesce"), "requires at least 1"),
        (op("upper", col("a"), col("b")), "requires 1 arguments"),
        (op("lower", col("a"), col("b")), "requires 1 arguments"),
        (op("trim", col("a"), col("b")), "requires 1 arguments"),
    ],
)
def test_operation_argument_validation(expression, message) -> None:
    with pytest.raises(ValueError, match=message):
        ExpressionBuilder().build(expression)


def test_expression_builder_rejects_unsupported_expression_type() -> None:
    with pytest.raises(TypeError, match="Unsupported expression type"):
        ExpressionBuilder().build(object())


def test_operation_expression_rejects_invalid_operation() -> None:
    with pytest.raises(ValidationError):
        OperationExpression(op="invalid", args=[])


@pytest.mark.parametrize(
    ("operator", "expected_ids"),
    [
        ("=", [2]),
        ("!=", [1, 3]),
        (">", [3]),
        (">=", [2, 3]),
        ("<", [1]),
        ("<=", [1, 2]),
    ],
)
def test_comparison_conditions_numeric_operators(operator, expected_ids) -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "value": [10, 20, 30],
        }
    )

    condition = ComparisonCondition(
        left=col("value"),
        operator=operator,
        right=val(20),
    )

    result = filter_with_condition(condition, df)

    assert result["id"].to_list() == expected_ids


@pytest.mark.parametrize(
    ("operator", "expected_ids"),
    [
        ("contains", [1, 3]),
        ("starts_with", [1, 3]),
        ("ends_with", [1]),
    ],
)
def test_comparison_conditions_string_operators(operator, expected_ids) -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "text": ["alpha", "beta", "alphabet"],
        }
    )

    condition = ComparisonCondition(
        left=col("text"),
        operator=operator,
        right=val("alpha"),
    )

    result = filter_with_condition(condition, df)

    assert result["id"].to_list() == expected_ids


def test_is_null_condition() -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "value": [None, "x", None],
        }
    )

    condition = ComparisonCondition(
        left=col("value"),
        operator="is_null",
    )

    result = filter_with_condition(condition, df)

    assert result["id"].to_list() == [1, 3]


def test_is_not_null_condition() -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "value": [None, "x", None],
        }
    )

    condition = ComparisonCondition(
        left=col("value"),
        operator="is_not_null",
    )

    result = filter_with_condition(condition, df)

    assert result["id"].to_list() == [2]


def test_is_in_condition() -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "value": ["A", "B", "C", "D"],
        }
    )

    condition = ComparisonCondition(
        left=col("value"),
        operator="is_in",
        right=val(["A", "C"]),
    )

    result = filter_with_condition(condition, df)

    assert result["id"].to_list() == [1, 3]


def test_and_condition() -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "value": [10, 20, 30, 40],
            "category": ["A", "A", "B", "B"],
        }
    )

    condition = AndCondition(
        logic="and",
        conditions=[
            ComparisonCondition(left=col("value"), operator=">", right=val(15)),
            ComparisonCondition(left=col("category"), operator="=", right=val("B")),
        ],
    )

    result = filter_with_condition(condition, df)

    assert result["id"].to_list() == [3, 4]


def test_or_condition() -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "value": [10, 20, 30, 40],
        }
    )

    condition = OrCondition(
        logic="or",
        conditions=[
            ComparisonCondition(left=col("value"), operator="<", right=val(15)),
            ComparisonCondition(left=col("value"), operator=">", right=val(35)),
        ],
    )

    result = filter_with_condition(condition, df)

    assert result["id"].to_list() == [1, 4]


def test_not_condition() -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "value": ["A", "B", "A"],
        }
    )

    condition = NotCondition(
        logic="not",
        condition=ComparisonCondition(
            left=col("value"),
            operator="=",
            right=val("A"),
        ),
    )

    result = filter_with_condition(condition, df)

    assert result["id"].to_list() == [2]


def test_nested_logical_condition() -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "value": [10, 20, 30, 40, 50],
            "category": ["A", "A", "B", "B", "C"],
        }
    )

    condition = AndCondition(
        logic="and",
        conditions=[
            OrCondition(
                logic="or",
                conditions=[
                    ComparisonCondition(left=col("category"), operator="=", right=val("A")),
                    ComparisonCondition(left=col("category"), operator="=", right=val("B")),
                ],
            ),
            ComparisonCondition(left=col("value"), operator=">=", right=val(30)),
        ],
    )

    result = filter_with_condition(condition, df)

    assert result["id"].to_list() == [3, 4]


@pytest.mark.parametrize(
    "operator",
    [
        "=",
        "!=",
        ">",
        ">=",
        "<",
        "<=",
        "contains",
        "starts_with",
        "ends_with",
        "is_in",
    ],
)
def test_comparison_operator_requires_right_expression(operator) -> None:
    condition = ComparisonCondition(
        left=col("value"),
        operator=operator,
    )

    with pytest.raises(ValueError, match="requires right expression"):
        ConditionBuilder().build(condition)


def test_and_condition_requires_at_least_one_child() -> None:
    condition = AndCondition(logic="and", conditions=[])

    with pytest.raises(ValueError, match="requires at least one child condition"):
        ConditionBuilder().build(condition)


def test_or_condition_requires_at_least_one_child() -> None:
    condition = OrCondition(logic="or", conditions=[])

    with pytest.raises(ValueError, match="requires at least one child condition"):
        ConditionBuilder().build(condition)


def test_condition_builder_rejects_unsupported_condition_type() -> None:
    with pytest.raises(TypeError, match="Unsupported condition type"):
        ConditionBuilder().build(object())


def test_comparison_condition_rejects_invalid_operator() -> None:
    with pytest.raises(ValidationError):
        ComparisonCondition(
            left=col("value"),
            operator="invalid",
            right=val(1),
        )


def test_condition_can_use_operation_expression_on_left_side() -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "a": [5, 10, 15],
            "b": [5, 10, 20],
        }
    )

    condition = ComparisonCondition(
        left=op("add", col("a"), col("b")),
        operator=">",
        right=val(25),
    )

    result = filter_with_condition(condition, df)

    assert result["id"].to_list() == [3]


def test_condition_can_use_operation_expression_on_right_side() -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "a": [10, 20, 30],
            "b": [5, 10, 15],
        }
    )

    condition = ComparisonCondition(
        left=col("a"),
        operator="=",
        right=op("multiply", col("b"), val(2)),
    )

    result = filter_with_condition(condition, df)

    assert result["id"].to_list() == [1, 2, 3]
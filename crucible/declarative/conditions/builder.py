from __future__ import annotations

from functools import reduce
from operator import and_, or_
from typing import Callable

import polars as pl

from crucible.declarative.conditions.models import (
    AndCondition,
    ComparisonCondition,
    Condition,
    NotCondition,
    OrCondition,
)
from crucible.declarative.expressions import ExpressionBuilder


class ConditionBuilder:
    """
    Builds Polars expressions from declarative condition definitions.

    The builder converts condition models such as
    [`ComparisonCondition`][crucible.declarative.conditions.models.ComparisonCondition],
    [`AndCondition`][crucible.declarative.conditions.models.AndCondition],
    [`OrCondition`][crucible.declarative.conditions.models.OrCondition],
    and [`NotCondition`][crucible.declarative.conditions.models.NotCondition]
    into executable `polars.Expr` objects.

    This component is used by filtering steps to translate user-defined
    workflow conditions into expressions that can be evaluated by Polars.

    Example:
        ```python
        condition = ComparisonCondition(
            left=ColumnExpression(column="country"),
            operator="=",
            right=ValueExpression(value="PL"),
        )

        expr = ConditionBuilder().build(condition)
        ```
    """

    def __init__(self) -> None:
        """
        Initialize the condition builder.

        Internally creates an
        [`ExpressionBuilder`][crucible.declarative.expressions.ExpressionBuilder]
        used to translate condition operands into Polars expressions.
        """
        self.expression_builder = ExpressionBuilder()

    def build(self, condition: Condition) -> pl.Expr:
        """
        Convert a declarative condition into a Polars expression.

        Supported condition types:

        - comparison conditions
        - logical AND conditions
        - logical OR conditions
        - logical NOT conditions

        Args:
            condition:
                Declarative condition definition.

        Returns:
            Equivalent Polars expression.

        Raises:
            TypeError:
                If the condition type is not supported.
        """
        if isinstance(condition, ComparisonCondition):
            return self._build_comparison(condition)

        if isinstance(condition, AndCondition):
            return self._combine(condition.conditions, and_)

        if isinstance(condition, OrCondition):
            return self._combine(condition.conditions, or_)

        if isinstance(condition, NotCondition):
            return ~self.build(condition.condition)

        raise TypeError(
            f"Unsupported condition type: {type(condition).__name__}"
        )

    def _build_comparison(self, condition: ComparisonCondition) -> pl.Expr:
        """
        Build a comparison expression.

        Supported operators:

        - `=`
        - `!=`
        - `>`
        - `>=`
        - `<`
        - `<=`
        - `contains`
        - `starts_with`
        - `ends_with`
        - `is_null`
        - `is_not_null`
        - `is_in`

        Args:
            condition:
                Comparison condition definition.

        Returns:
            Equivalent Polars expression.

        Raises:
            ValueError:
                If an unsupported operator is provided.
        """
        left = self.expression_builder.build(condition.left)
        right = (
            self.expression_builder.build(condition.right)
            if condition.right is not None
            else None
        )

        match condition.operator:
            case "=":
                self._require_right(condition)
                return left == right
            case "!=":
                self._require_right(condition)
                return left != right
            case ">":
                self._require_right(condition)
                return left > right
            case ">=":
                self._require_right(condition)
                return left >= right
            case "<":
                self._require_right(condition)
                return left < right
            case "<=":
                self._require_right(condition)
                return left <= right
            case "contains":
                self._require_right(condition)
                return left.str.contains(right)
            case "starts_with":
                self._require_right(condition)
                return left.str.starts_with(right)
            case "ends_with":
                self._require_right(condition)
                return left.str.ends_with(right)
            case "is_null":
                return left.is_null()
            case "is_not_null":
                return left.is_not_null()
            case "is_in":
                self._require_right(condition)
                return left.is_in(right)
            case _:
                raise ValueError(
                    f"Unsupported comparison operator: {condition.operator}"
                )

    def _combine(self, conditions: list[Condition], combiner: Callable[[pl.Expr, pl.Expr], pl.Expr]) -> pl.Expr:
        """
        Combine multiple conditions using a logical operator.

        Args:
            conditions:
                Child conditions to combine.

            combiner:
                Logical operator used to combine generated expressions.

        Returns:
            Combined Polars expression.

        Raises:
            ValueError:
                If no child conditions are provided.
        """
        if not conditions:
            raise ValueError(
                "Logical condition requires at least one child condition."
            )

        return reduce(
            combiner,
            [self.build(condition) for condition in conditions],
        )

    def _require_right(self, condition: ComparisonCondition) -> None:
        """
        Validate that a comparison operator has a right operand.

        Args:
            condition:
                Comparison condition to validate.

        Raises:
            ValueError:
                If the operator requires a right operand but none was supplied.
        """
        if condition.right is None:
            raise ValueError(
                f"Operator '{condition.operator}' requires right expression."
            )
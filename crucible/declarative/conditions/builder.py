from __future__ import annotations

from functools import reduce
from operator import and_, or_

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
    def __init__(self) -> None:
        self.expression_builder = ExpressionBuilder()

    def build(self, condition: Condition) -> pl.Expr:
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

    def _combine(self, conditions: list[Condition], combiner) -> pl.Expr:
        if not conditions:
            raise ValueError(
                "Logical condition requires at least one child condition."
            )

        return reduce(
            combiner,
            [self.build(condition) for condition in conditions],
        )

    def _require_right(self, condition: ComparisonCondition) -> None:
        if condition.right is None:
            raise ValueError(
                f"Operator '{condition.operator}' requires right expression."
            )
from typing import Any, Literal

import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepConfig


OPERATORS = {
    "=": lambda col, value: col == value,
    "!=": lambda col, value: col != value,
    ">": lambda col, value: col > value,
    ">=": lambda col, value: col >= value,
    "<": lambda col, value: col < value,
    "<=": lambda col, value: col <= value,
    "contains": lambda col, value: col.str.contains(value),
    "starts_with": lambda col, value: col.str.starts_with(value),
    "ends_with": lambda col, value: col.str.ends_with(value),
    "is_null": lambda col, value: col.is_null(),
    "is_not_null": lambda col, value: col.is_not_null(),
    "is_in": lambda col, value: col.is_in(value),
}

class FilterCondition(BaseModel):
    column: str
    operator: str
    value: Any = None


class FilterRowsConfig(BaseModel):
    logic: Literal["and", "or"] = "and"
    conditions: list[FilterCondition]

class FilterRowsStep(Step):
    key = "filter_rows"
    name = "Filter Rows"
    description = "Filter rows based on a condition applied to a column."
    config_model = FilterRowsConfig

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        expressions = []

        for condition in self.config.conditions:
            op = OPERATORS[condition.operator]
            expressions.append(
                op(pl.col(condition.column), condition.value)
            )

        if self.config.logic == "and":
            predicate = expressions[0]
            for expr in expressions[1:]:
                predicate &= expr
        else:
            predicate = expressions[0]
            for expr in expressions[1:]:
                predicate |= expr

        return data.filter(predicate)
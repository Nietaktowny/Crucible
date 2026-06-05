from typing import Any

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

class SelectColumnsConfig(BaseModel):
    column: str
    operator: str
    value: Any

class FilterRowsStep(Step):
    key = "filter_rows"
    name = "Filter Rows"
    description = "Filter rows based on a condition applied to a column."
    config_model = SelectColumnsConfig

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        column = self.config.column
        operator = self.config.operator
        value = getattr(self.config, "value", None)

        try:
            op = OPERATORS[operator]
        except KeyError:
            raise ValueError(f"Unsupported filter operator: {operator}") from None

        return data.filter(op(pl.col(column), value))
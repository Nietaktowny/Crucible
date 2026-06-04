from typing import Any

import polars as pl

from crucible.models import Step


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


class FilterRowsStep(Step):
    key = "filter_rows"

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        column = self.config.column
        operator = self.config.operator
        value = getattr(self.config, "value", None)

        try:
            op = OPERATORS[operator]
        except KeyError:
            raise ValueError(f"Unsupported filter operator: {operator}") from None

        return data.filter(op(pl.col(column), value))
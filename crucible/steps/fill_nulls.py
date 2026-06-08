from typing import Any

import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext


class FillNullsConfig(BaseModel):
    columns: list[str]
    value: Any


class FillNullsStep(Step):
    key = "fill_nulls"
    name = "Fill Nulls"
    description = "Replace null values with a specified value."
    config_model = FillNullsConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        expressions = [
            pl.col(column).fill_null(self.config.value)
            for column in self.config.columns
        ]

        return data.with_columns(expressions)
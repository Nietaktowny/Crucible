import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext


class FillDownConfig(BaseModel):
    columns: list[str]


class FillDownStep(Step):
    key = "fill_down"
    name = "Fill Down"
    description = "Fill null values with the previous non-null value."
    config_model = FillDownConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        expressions = [
            pl.col(column).forward_fill()
            for column in self.config.columns
        ]

        return data.with_columns(expressions)
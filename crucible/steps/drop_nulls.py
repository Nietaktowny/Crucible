import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext


class DropNullsConfig(BaseModel):
    columns: list[str] | None = None


class DropNullsStep(Step):
    key = "drop_nulls"
    name = "Drop Nulls"
    description = "Remove rows containing null values."
    config_model = DropNullsConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        return data.drop_nulls(
            subset=self.config.columns,
        )
from typing import Any, Literal

import polars as pl
from pydantic import BaseModel, model_validator

from crucible.models import Step, StepExecutionContext


class CreateColumnConfig(BaseModel):
    name: str

    value: Any | None = None
    expression: str | None = None

    @model_validator(mode="after")
    def validate_configuration(self):
        if self.value is not None and self.expression is not None:
            raise ValueError("Use either value or expression, not both.")

        if self.value is None and self.expression is None:
            raise ValueError("Either value or expression must be provided.")

        return self


class CreateColumnStep(Step):
    key = "create_column"
    name = "Create Column"
    description = "Create a new column from a literal value or expression."
    config_model = CreateColumnConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        if self.config.value is not None:
            expression = pl.lit(self.config.value)
        else:
            expression = pl.sql_expr(self.config.expression)

        return data.with_columns(
            expression.alias(self.config.name)
        )
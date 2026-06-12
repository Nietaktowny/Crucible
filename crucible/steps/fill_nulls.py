from typing import Any

import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingColumnsGuard


class FillNullsConfig(BaseModel):
    columns: list[str]
    value: Any


class FillNullsStep(Step):
    key = "fill_nulls"
    name = "Fill Nulls"
    description = "Replace null values with a specified value."
    config_model = FillNullsConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [MissingColumnsGuard(self.config.columns)]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        expressions = [
            pl.col(column).fill_null(self.config.value)
            for column in self.config.columns
        ]

        result = data.df.with_columns(expressions)
        return FrameContext(df=result)
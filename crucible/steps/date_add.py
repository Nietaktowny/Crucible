from typing import Literal

import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext


class DateAddConfig(BaseModel):
    column: str

    value: int
    unit: Literal[
        "days",
        "hours",
        "minutes",
        "seconds",
        "milliseconds",
    ] = "days"

    output_column: str | None = None


class DateAddStep(Step):
    key = "date_add"
    name = "Date Add"
    description = "Add or subtract duration from a date or datetime column."
    config_model = DateAddConfig

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        output_column = self.config.output_column or self.config.column

        expression = (
            pl.col(self.config.column)
            + self._build_duration()
        ).alias(output_column)

        result = data.df.with_columns(expression)
        return FrameContext(df=result, schema=data.schema)

    def _build_duration(self) -> pl.Expr:
        match self.config.unit:
            case "days":
                return pl.duration(days=self.config.value)
            case "hours":
                return pl.duration(hours=self.config.value)
            case "minutes":
                return pl.duration(minutes=self.config.value)
            case "seconds":
                return pl.duration(seconds=self.config.value)
            case "milliseconds":
                return pl.duration(milliseconds=self.config.value)
            case _:
                raise ValueError(f"Unsupported unit: {self.config.unit}")
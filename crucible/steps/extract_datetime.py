from typing import Literal

import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard


class ExtractDateTimeConfig(BaseModel):
    column: str
    extract: Literal["date", "time"]

    output_column: str | None = None


class ExtractDateTimeStep(Step):
    key = "extract_date_time"
    name = "Extract Date/Time"
    description = "Extract date or time from a datetime column."
    config_model = ExtractDateTimeConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [
            MissingColumnsGuard([self.config.column]),
            ColumnsTypeGuard({self.config.column: ["Datetime"]}),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        output_column = self.config.output_column or f"{self.config.column}_{self.config.extract}"

        expression = self._build_expression().alias(output_column)

        result = data.df.with_columns(expression)
        return FrameContext(df=result, schema=data.schema)

    def _build_expression(self) -> pl.Expr:
        column = pl.col(self.config.column)

        match self.config.extract:
            case "date":
                return column.dt.date()
            case "time":
                return column.dt.time()
            case _:
                raise ValueError(f"Unsupported extraction: {self.config.extract}")
from typing import Literal

import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext


class ParseDateTimeConfig(BaseModel):
    column: str
    target_type: Literal["date", "datetime", "time"]

    format: str | None = None
    output_column: str | None = None

    strict: bool = False


class ParseDateTimeStep(Step):
    key = "parse_datetime"
    name = "Parse Date/Time"
    description = "Parse a text column into date, datetime, or time."
    config_model = ParseDateTimeConfig

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        dtype = self._get_dtype()
        output_column = self.config.output_column or self.config.column

        expression = (
            pl.col(self.config.column)
            .str.strptime(
                dtype=dtype,
                format=self.config.format,
                strict=self.config.strict,
            )
            .alias(output_column)
        )

        result = data.df.with_columns(expression)
        return FrameContext(df=result, schema=data.schema)

    def _get_dtype(self) -> type[pl.Date] | type[pl.Datetime] | type[pl.Time]:
        match self.config.target_type:
            case "date":
                return pl.Date
            case "datetime":
                return pl.Datetime
            case "time":
                return pl.Time
            case _:
                raise ValueError(
                    f"Unsupported target_type: {self.config.target_type}"
                )
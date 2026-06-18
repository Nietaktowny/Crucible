from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class ExtractDateTimePartConfig(BaseModel):
    column: ColumnName = Field(
        description="Column to extract datetime part from",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )
    part: Literal[
        "year",
        "month",
        "day",
        "week",
        "weekday",
        "hour",
        "minute",
        "second",
    ] = Field(
        description="Part of datetime to extract",
        json_schema_extra=build_schema(
            type_='literal-value',
            editor='select',
            source='enum'
        )
    )

    output_column: ColumnName | None = Field(
        default=None,
        description="Output column. If not specified auto generated name will be used",
        json_schema_extra=build_schema(
            type_='column-name',
            role='output-column',
            editor='text'
        )
    )


class ExtractDateTimePartStep(Step):
    key = "extract_datetime_part"
    name = "Extract Date/Time Part"
    description = "Extract a selected part from a date, datetime, or time column."
    config_model = ExtractDateTimePartConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard([self.config.column]),
            ColumnsTypeGuard({self.config.column: ["Date", "Datetime", "Time"]}),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        output_column = self.config.output_column or f"{self.config.column}_{self.config.part}"

        expression = self._build_expression().alias(output_column)

        result = data.df.with_columns(expression)
        return FrameContext(df=result)

    def _build_expression(self) -> pl.Expr:
        column = pl.col(self.config.column)

        match self.config.part:
            case "year":
                return column.dt.year()
            case "month":
                return column.dt.month()
            case "day":
                return column.dt.day()
            case "week":
                return column.dt.week()
            case "weekday":
                return column.dt.weekday()
            case "hour":
                return column.dt.hour()
            case "minute":
                return column.dt.minute()
            case "second":
                return column.dt.second()
            case _:
                raise ValueError(f"Unsupported date/time part: {self.config.part}")
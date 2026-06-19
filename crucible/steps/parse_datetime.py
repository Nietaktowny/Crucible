from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class ParseDateTimeConfig(BaseModel):
    column: ColumnName = Field(
        description="Column with datetime values to parse",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )
    target_type: Literal["date", "datetime", "time"] = Field(
        description="What type of value the column holds",
        json_schema_extra=build_schema(
            type_='literal-value',
            editor='select',
            source='enum'
        )
    )

    format: str | None = Field(
        description="Datetime string format to parse",
        json_schema_extra=build_schema(
            editor='text'
        )
    )
    output_column: ColumnName | None = Field(
        default=None,
        description="Column with datetime values to parse",
        json_schema_extra=build_schema(
            type_='column-name',
            role='output-column',
            editor='text'
        )
    )

    strict: bool = Field(
        default=False,
        description="Enable strict mode",
        json_schema_extra=build_schema(
            editor='checkbox'
        )
    )


class ParseDateTimeStep(Step):
    key = "parse_datetime"
    name = "Parse Date/Time"
    description = "Parse a text column into date, datetime, or time."
    config_model = ParseDateTimeConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard([self.config.column]),
            ColumnsTypeGuard({self.config.column: ["String"]}),
        ]

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
        return FrameContext(df=result)

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
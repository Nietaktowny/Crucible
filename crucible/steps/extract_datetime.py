from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class ExtractDateTimeConfig(BaseModel):
    column: ColumnName = Field(
        description="Column to extract datetime part from",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )
    extract: Literal["date", "time"] = Field(
        description="Whether to extract date or time from datetime",
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


class ExtractDateTimeStep(Step):
    key = "extract_date_time"
    name = "Extract Date/Time"
    description = "Extract date or time from a datetime column."
    config_model = ExtractDateTimeConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [
            LazyFrameInstanceGuard(),
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
        return FrameContext(df=result)

    def _build_expression(self) -> pl.Expr:
        column = pl.col(self.config.column)

        match self.config.extract:
            case "date":
                return column.dt.date()
            case "time":
                return column.dt.time()
            case _:
                raise ValueError(f"Unsupported extraction: {self.config.extract}")
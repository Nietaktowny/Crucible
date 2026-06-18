from typing import Any

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema


class FillNullsConfig(BaseModel):
    columns: list[ColumnName] = Field(
        description="List of columns to replace nulls in",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )
    value: Any = Field(
        description="Value to replace nulls with",
        json_schema_extra=build_schema(
            editor='text'
        )
    )


class FillNullsStep(Step):
    key = "fill_nulls"
    name = "Fill Nulls"
    description = "Replace null values with a specified value."
    config_model = FillNullsConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(self.config.columns),
        ]

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
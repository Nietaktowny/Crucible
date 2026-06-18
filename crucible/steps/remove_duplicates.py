from typing import Literal

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

import polars as pl
from pydantic import BaseModel, Field


class RemoveDuplicatesConfig(BaseModel):
    columns: list[ColumnName] | None = Field(
        default=None,
        description='Columns to remove duplicates in. If not specified, then duplicates will be removed in whole dataset',
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )
    keep: Literal['first', 'last'] = Field(
        default="first",
        description="Whether to keep last or first occurrence of value",
        json_schema_extra=build_schema(
            type_='literal-value',
            source='enum',
            editor='select'
        )
    )

class RemoveDuplicatesStep(Step):
    key = "remove_duplicates"
    name = "Remove Duplicates"
    description = "Remove duplicate rows."
    config_model = RemoveDuplicatesConfig

    def guards(self) -> list[StepGuardProtocol]:
        if self.config.columns:
            return [
                LazyFrameInstanceGuard(),
                MissingColumnsGuard(self.config.columns),
            ]
        return [LazyFrameInstanceGuard()]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        result = data.df.unique(
            subset=self.config.columns,
            keep=self.config.keep,
        )
        return FrameContext(df=result)
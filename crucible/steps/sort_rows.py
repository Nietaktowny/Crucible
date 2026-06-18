from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema
class SortColumnConfig(BaseModel):
    name: ColumnName = Field(
        description="Column to use for sorting",
        json_schema_extra=build_schema(
            type_='column-name',
            role='sort-column',
            source='input-schema',
            editor='column-select'
        )
    )
    direction: Literal['asc', 'desc'] = Field(
        default='asc',
        description='Sorting direction',
        json_schema_extra=build_schema(
            type_='literal-value',
            source='enum',
            editor='select'
        )
    )

class SortRowsConfig(BaseModel):
    columns: list[SortColumnConfig]

class SortRowsStep(Step):
    key = "sort_rows"
    name = "Sort Rows"
    description = "Sort rows based on specified columns and sort directions."
    config_model = SortRowsConfig

    def guards(self) -> list[StepGuardProtocol]:
        sort_columns = [column.name for column in self.config.columns]
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(sort_columns),
        ]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        by = [column.name for column in self.config.columns]

        descending = [
            column.direction.lower() == "desc"
            for column in self.config.columns
        ]

        result = data.df.sort(
            by=by,
            descending=descending,
        )
        return FrameContext(df=result)
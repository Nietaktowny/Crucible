from typing import Literal

import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext

class SortColumnConfig(BaseModel):
    name: str
    direction: Literal['asc', 'desc'] = 'asc'

class SortRowsConfig(BaseModel):
    columns: list[SortColumnConfig]

class SortRowsStep(Step):
    key = "sort_rows"
    name = "Sort Rows"
    description = "Sort rows based on specified columns and sort directions."
    config_model = SortRowsConfig

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
        return FrameContext(df=result, schema=data.schema)
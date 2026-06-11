from typing import Literal

from crucible.models import Step, StepExecutionContext, FrameContext

import polars as pl
from pydantic import BaseModel


class RemoveDuplicatesConfig(BaseModel):
    columns: list[str] | None = None
    keep: Literal['first', 'last'] = "first"

class RemoveDuplicatesStep(Step):
    key = "remove_duplicates"
    name = "Remove Duplicates"
    description = "Remove duplicate rows."
    config_model = RemoveDuplicatesConfig

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        result = data.df.unique(
            subset=self.config.columns,
            keep=self.config.keep,
        )
        return FrameContext(df=result, schema=data.schema)
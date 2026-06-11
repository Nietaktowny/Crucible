from typing import Literal, Any

from crucible.models import Step, StepExecutionContext, FrameContext

import polars as pl
from pydantic import BaseModel, computed_field

from rich.pretty import pprint

class ConcatConfig(BaseModel):
    how: Literal["vertical", "diagonal", "horizontal"] = "vertical"

class ConcatStep(Step):
    key = "concat"
    name = "Concatenate"
    description = "Append rows from multiple sources"
    config_model = ConcatConfig

    def execute(self, data: FrameContext, context: StepExecutionContext | None = None) -> FrameContext:
        extra_inputs = list(context.extra_inputs.values())
        context.extra_inputs.clear()

        # Extract LazyFrames from FrameContext objects if needed
        frames = [data.df]
        for item in extra_inputs:
            if isinstance(item, FrameContext):
                frames.append(item.df)
            else:
                frames.append(item)

        result = pl.concat(
            frames,
            how=self.config.how,
        )
        return FrameContext(df=result, schema=data.schema)
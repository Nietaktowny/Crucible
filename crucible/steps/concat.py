from typing import Literal, Any

from crucible.models import Step, StepExecutionContext

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

    def execute(self, data: pl.LazyFrame, context: StepExecutionContext | None = None) -> pl.LazyFrame:
        extra_inputs = list(context.extra_inputs.values())
        context.extra_inputs.clear()

        return pl.concat(
            [data, *extra_inputs],
            how=self.config.how,
        )
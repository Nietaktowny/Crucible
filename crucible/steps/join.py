from typing import Literal, Any

from crucible.models import Step, StepExecutionContext

import polars as pl
from pydantic import BaseModel, computed_field

class JoinConfig(BaseModel):
    left_on:  str | list[str]
    right_on: str | list[str]
    how: Literal["left", "inner", "right", "full", "anti", "cross"] = "left"

class JoinStep(Step):
    key = "join"
    name = "Join"
    description = "Join two datasets"
    config_model = JoinConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        right = context.extra_inputs.pop("right")

        if self.config.how == "cross":
            return data.join(
                other=right,
                how="cross",
            )

        return data.join(
            other=right,
            left_on=self.config.left_on,
            right_on=self.config.right_on,
            how=self.config.how,
        )
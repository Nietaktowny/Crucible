from typing import Literal

import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingColumnsGuard

class JoinConfig(BaseModel):
    left_on: str | list[str]
    right_on: str | list[str]
    how: Literal["left", "inner", "right", "full", "anti", "cross"] = "left"

class JoinStep(Step):
    key = "join"
    name = "Join"
    description = "Join two datasets"
    config_model = JoinConfig

    def guards(self) -> list[StepGuardProtocol]:
        if self.config.how == "cross":
            return []
        columns_to_check = []
        if isinstance(self.config.left_on, list):
            columns_to_check.extend(self.config.left_on)
        else:
            columns_to_check.append(self.config.left_on)
        return [MissingColumnsGuard(columns_to_check)]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext | None = None,
    ) -> FrameContext:
        if context is None:
            raise ValueError("JoinStep requires execution context")

        right_context = context.extra_inputs.pop("right", None)

        if right_context is None:
            raise ValueError(
                "JoinStep requires extra input named 'right'. "
                f"Available extra inputs: {list(context.extra_inputs.keys())}"
            )

        right = right_context.df if isinstance(right_context, FrameContext) else right_context

        if self.config.how == "cross":
            result = data.df.join(other=right, how="cross")
        else:
            result = data.df.join(
                other=right,
                left_on=self.config.left_on,
                right_on=self.config.right_on,
                how=self.config.how,
            )

        return FrameContext(df=result)
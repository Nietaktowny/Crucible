from typing import Literal

from crucible.models import (
    Step,
    StepExecutionContext,
    FrameContext,
    StepGuardProtocol
)
from crucible.errors import LazyFrameInstanceGuard

import polars as pl
from pydantic import BaseModel

class ConcatConfig(BaseModel):
    """
    Configuration for concatenating multiple source frames into one.

    `how` controls the Polars concatenation strategy (matching
    `polars.concat`'s `how` argument): "vertical" stacks rows and requires
    matching schemas, "diagonal" stacks rows and reconciles mismatched
    schemas, and "horizontal" combines columns side by side.
    """

    context_keys: list[str] | None = None
    """Explicit sources to consume, or all context inputs for legacy workflows."""

    how: Literal["vertical", "diagonal", "horizontal"] = "vertical"

class ConcatStep(Step):
    """
    Step that concatenates the primary frame with every extra source frame.

    Pulls all frames currently stored in `context.extra_inputs`, clears that
    store, and concatenates them together with the primary input frame using
    `polars.concat` and the configured `how` strategy. This is a
    multi-source-style step: it relies on other steps (e.g. `read_csv` with
    `context_store`) having populated `context.extra_inputs` beforehand.
    """

    key = "concat"
    name = "Concatenate"
    description = "Append rows from multiple sources"
    config_model = ConcatConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards ensuring the input frame is a valid LazyFrame.

        Returns:
            List containing a `LazyFrameInstanceGuard`.
        """
        return [LazyFrameInstanceGuard()]

    def execute(self, data: FrameContext, context: StepExecutionContext | None = None) -> FrameContext:
        """
        Concatenate the primary frame with all extra input frames.

        Args:
            data:
                Primary frame context; its `df` is the first frame
                concatenated.

            context:
                Execution context whose `extra_inputs` values (each either a
                `FrameContext` or a raw `LazyFrame`) are concatenated after
                `data`. `extra_inputs` is cleared as a side effect.

        Returns:
            A new `FrameContext` wrapping the concatenated result.
        """
        keys = self.config.context_keys
        if keys is None:
            keys = list(context.extra_inputs)
        missing = [key for key in keys if key not in context.extra_inputs]
        if missing:
            raise ValueError(f"Append sources not found: {missing}")
        extra_inputs = [context.extra_inputs.pop(key) for key in dict.fromkeys(keys)]

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
        return FrameContext(df=result)
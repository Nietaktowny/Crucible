from typing import Literal

from crucible.models import Step, FrameContext, StepGuardProtocol
import polars as pl
from pydantic import BaseModel, Field

from crucible.models import StepExecutionContext
from crucible.schema import build_schema
class LimitRowsConfig(BaseModel):
    """Configuration for [`LimitRowsStep`][crucible.steps.limit_rows.LimitRowsStep]."""

    limit: int = Field(
        description="Number of max rows to return",
        json_schema_extra=build_schema(
            editor='number'
        )
    )
    mode: Literal['head', 'tail'] = Field(
        description="Whether to select last or first n rows",
        json_schema_extra=build_schema(
            type_='literal-value',
            source='enum',
            editor='select'
        )
    )

class LimitRowsStep(Step):
    """
    Step that truncates the frame to its first or last N rows.

    Depending on `mode`, either `LazyFrame.head` or `LazyFrame.tail` is used
    to keep at most `limit` rows. No guards are declared, so this step does
    not require the input to be a `LazyFrame` or have any specific columns.
    """

    key = "limit_rows"
    name = "Limit rows"
    description = "Limit rows to first or last n rows"
    config_model = LimitRowsConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before limiting rows.

        Returns:
            An empty list; this step declares no runtime guards.
        """
        return []

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        """
        Keep only the first or last `limit` rows of the frame.

        Args:
            data:
                Frame context whose `df` is truncated.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the truncated lazy frame.

        Raises:
            ValueError:
                If `mode` is neither `"head"` nor `"tail"`.
        """
        if self.config.mode == 'head':
            result = data.df.head(self.config.limit)
        elif self.config.mode == 'tail':
            result = data.df.tail(self.config.limit)
        else:
            raise ValueError(f"Unknown limit rows mode for LimitRowsStep, passed: {self.config.mode}. Expected one of: {['head', 'tail']}")
        return FrameContext(df=result)
            
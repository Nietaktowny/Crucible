from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema
class JoinConfig(BaseModel):
    """
    Configuration for joining the primary frame with a "right" source frame.

    `left_on`/`right_on` are ignored when `how` is "cross", since a cross join
    has no join keys.
    """

    left_on: ColumnName | list[ColumnName] = Field(
        description="Column or list of columns to join on left side",
        json_schema_extra=build_schema(
            type_='column-name',
            role='join-left-key',
            source='left-schema',
            editor='column-multiselect'
        )
    )
    right_on: ColumnName | list[ColumnName] = Field(
        description="Column or list of columns to join on right side",
        json_schema_extra=build_schema(
            type_='column-name',
            role='join-right-key',
            source='right-schema',
            editor='column-multiselect'
        )
    )
    how: Literal["left", "inner", "right", "full", "anti", "cross"] = Field(
        default="left",
        description="How to join two dataframes",
        json_schema_extra=build_schema(
            type_='literal-value',
            source='enum',
            editor='select'
        )
    )

class JoinStep(Step):
    """
    Step that joins the primary frame with a "right" frame from the execution
    context.

    Looks up the source frame named "right" in `context.extra_inputs` and
    joins it with the primary frame using `polars.LazyFrame.join`. All join
    types supported by Polars are available via `how`, including "cross",
    which ignores `left_on`/`right_on` entirely.
    """

    key = "join"
    name = "Join"
    description = "Join two datasets"
    config_model = JoinConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards for the configured join.

        For a "cross" join no guards are needed since there are no join keys
        to validate. Otherwise, returns a `LazyFrameInstanceGuard` plus a
        `MissingColumnsGuard` checking that all `left_on` columns exist in the
        primary frame's schema.

        Returns:
            List of guards appropriate for the configured `how` value.
        """
        if self.config.how == "cross":
            return []
        columns_to_check = []
        if isinstance(self.config.left_on, list):
            columns_to_check.extend(self.config.left_on)
        else:
            columns_to_check.append(self.config.left_on)
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(columns_to_check),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext | None = None,
    ) -> FrameContext:
        """
        Join the primary frame with the "right" frame from the context.

        Args:
            data:
                Primary (left) frame context.

            context:
                Execution context that must contain an extra input named
                "right" (either a `FrameContext` or a raw `LazyFrame`); it is
                popped from `context.extra_inputs` as a side effect.

        Returns:
            A new `FrameContext` wrapping the joined result.

        Raises:
            ValueError:
                If `context` is `None`, or if it has no extra input named
                "right".
        """
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
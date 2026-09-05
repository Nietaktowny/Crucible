import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class FillDownConfig(BaseModel):
    """Configuration for [`FillDownStep`][crucible.steps.fill_down.FillDownStep]."""

    columns: list[ColumnName]  = Field(
        description="List of columns to drop",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )


class FillDownStep(Step):
    """
    Step that propagates the last non-null value forward within a column.

    For each configured column, applies Polars' `forward_fill` expression so
    that a null cell takes the value of the nearest preceding non-null row.
    """

    key = "fill_down"
    name = "Fill Down"
    description = "Fill null values with the previous non-null value."
    config_model = FillDownConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before filling down.

        Returns:
            A [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard]
            ensuring the input is a Polars `LazyFrame`, and a
            [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard]
            ensuring every configured column exists in the frame schema.
        """
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(self.config.columns),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """
        Forward-fill null values in the configured columns.

        Args:
            data:
                Frame context whose `df` is forward-filled.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the frame with nulls forward-filled.
        """
        expressions = [
            pl.col(column).forward_fill()
            for column in self.config.columns
        ]

        result = data.df.with_columns(expressions)
        return FrameContext(df=result)
import polars as pl
from pydantic import BaseModel, Field

from crucible.errors.guards import LazyFrameInstanceGuard
from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class DropNullsConfig(BaseModel):
    """
    Configuration for [`DropNullsStep`][crucible.steps.drop_nulls.DropNullsStep].

    When `columns` is omitted, a row is dropped if any column contains a
    null value.
    """

    columns: list[ColumnName] | None = Field(
        default=None,
        description="List of columns to drop",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )


class DropNullsStep(Step):
    """
    Step that removes rows containing null values.

    Delegates to `LazyFrame.drop_nulls` with an optional `subset` of columns;
    when no subset is configured, any null in any column causes the row to
    be dropped.
    """

    key = "drop_nulls"
    name = "Drop Nulls"
    description = "Remove rows containing null values."
    config_model = DropNullsConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before dropping nulls.

        Returns:
            A [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard]
            always, plus a [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard]
            for the configured `columns` when a subset is specified.
        """
        if self.config.columns:
            return [
                LazyFrameInstanceGuard(),
                MissingColumnsGuard(self.config.columns),
        ]
        return [LazyFrameInstanceGuard()]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """
        Drop rows containing null values in the configured columns.

        Args:
            data:
                Frame context whose `df` has null-containing rows removed.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the filtered lazy frame.
        """
        result = data.df.drop_nulls(
            subset=self.config.columns,
        )
        return FrameContext(df=result)
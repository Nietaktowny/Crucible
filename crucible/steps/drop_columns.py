from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class DropColumnsConfig(BaseModel):
    """
    Configuration for dropping a set of columns from a frame.
    """

    columns: list[ColumnName]  = Field(
        description="List of columns to drop",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )


class DropColumnsStep(Step):
    """
    Step that removes the configured columns from the frame.

    Calls `polars.LazyFrame.drop` with the configured column list, leaving all
    other columns and row order untouched.
    """

    key = "drop_columns"
    name = "Drop columns"
    description = "Drop specified columns"
    config_model = DropColumnsConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards ensuring the input is a LazyFrame containing the
        columns to drop.

        Returns:
            List containing a `LazyFrameInstanceGuard` and a
            `MissingColumnsGuard` for the configured columns.
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
        Drop the configured columns from the frame.

        Args:
            data:
                Frame context whose `df` has the configured columns removed.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            A new `FrameContext` wrapping the frame with the configured
            columns removed.
        """
        result = data.df.drop(self.config.columns)
        return FrameContext(df=result)
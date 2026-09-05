from crucible.models import Step, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema
from pydantic import BaseModel, Field

from crucible.models import StepExecutionContext

class SelectColumnsConfig(BaseModel):
    """
    Configuration for selecting a subset of columns from a frame.
    """

    columns: list[ColumnName] = Field(
        description="Columns that should remain in the dataset.",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )

class SelectColumnsStep(Step):
    """
    Step that keeps only the configured columns in the frame.

    Calls `polars.LazyFrame.select` with the configured column list, dropping
    every other column and reordering the output to match the given order.
    """

    key = "select_columns"
    name = "Select Columns"
    description = "Select a subset of columns from the data."
    config_model = SelectColumnsConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards ensuring the input is a LazyFrame containing the
        configured columns.

        Returns:
            List containing a `LazyFrameInstanceGuard` and a
            `MissingColumnsGuard` for the configured columns.
        """
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(self.config.columns)
        ]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        """
        Select the configured columns from the frame.

        Args:
            data:
                Frame context whose `df` is selected down to the configured
                columns.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            A new `FrameContext` wrapping the frame with only the configured
            columns, in the configured order.
        """
        result = data.df.select(self.config.columns)
        return FrameContext(df=result)
import polars as pl
from pydantic import BaseModel, Field


from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema
class ReorderColumnsConfig(BaseModel):
    """
    Configuration for reordering the columns of a frame.

    `columns` must list every column that should remain; since it is applied
    via a `select`, any column not included is dropped rather than left in
    place.
    """

    columns: list[ColumnName] = Field(
        description="Columns order",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )
    
class ReorderColumnsStep(Step):
    """
    Step that reorders the frame's columns to match the configured order.

    Implemented as `polars.LazyFrame.select` with the configured column list,
    so the resulting frame contains exactly those columns, in that order; any
    column omitted from the list is dropped.
    """

    key = "reorder_columns"
    name = "Reorder Columns"
    description = "Reorder columns based on a specified list of column names."
    config_model = ReorderColumnsConfig

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
            MissingColumnsGuard(self.config.columns),
        ]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        """
        Reorder the frame's columns to match the configured order.

        Args:
            data:
                Frame context whose `df` is reordered.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            A new `FrameContext` wrapping the frame with columns in the
            configured order.
        """
        result = data.df.select(self.config.columns)
        return FrameContext(df=result)
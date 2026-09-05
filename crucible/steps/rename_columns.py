import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard

class RenameColumnsConfig(BaseModel):
    """
    Configuration for renaming columns of a frame.

    `mapping` maps existing column names to their new names.
    """

    mapping: dict[ColumnName, ColumnName]
class RenameColumnsStep(Step):
    """
    Step that renames columns of the frame according to the configured
    mapping.

    Calls `polars.LazyFrame.rename` with the configured mapping; columns not
    present in the mapping are left unchanged.
    """

    key = "rename_columns"
    name = "Rename Columns"
    description = "Rename columns based on a provided mapping."
    config_model = RenameColumnsConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards ensuring the input is a LazyFrame containing all
        columns referenced by the rename mapping.

        Returns:
            List containing a `LazyFrameInstanceGuard` and a
            `MissingColumnsGuard` for the mapping's source column names.
        """
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(list(self.config.mapping.keys())),
        ]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        """
        Rename the frame's columns according to the configured mapping.

        Args:
            data:
                Frame context whose `df` columns are renamed.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            A new `FrameContext` wrapping the frame with renamed columns.
        """
        result = data.df.rename(self.config.mapping)
        return FrameContext(df=result)
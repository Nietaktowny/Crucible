from pathlib import Path

from pydantic import BaseModel

from crucible.io import ExcelIOManager
from crucible.models import StepConfig, Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import LazyFrameInstanceGuard

import polars as pl

class WriteExcelConfig(BaseModel):
    """
    Configuration for writing a Polars frame to an Excel workbook.

    When `sheet` is left as `None`, the default worksheet name chosen by
    `polars.DataFrame.write_excel` (e.g. "Sheet1") is used.
    """

    path: Path
    sheet: str | None = None
    table_style: str = "Table Style Medium 1"

class WriteExcelStep(Step):
    """
    Step that writes the current frame to an Excel workbook.

    Delegates to [`ExcelIOManager`][crucible.io.ExcelIOManager], which collects
    the lazy frame and writes it as a formatted Excel table using the
    configured sheet name and table style. The input frame is returned
    unchanged so the write acts as a side effect.
    """

    key = "write_excel"
    name = "Write Excel File"
    description = "Write data to a Excel workbook."
    config_model = WriteExcelConfig

    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = ExcelIOManager(self.config.path, self.config.sheet)

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards ensuring the input frame is a valid LazyFrame.

        Returns:
            List containing a `LazyFrameInstanceGuard`.
        """
        return [LazyFrameInstanceGuard()]

    def execute(self, data: FrameContext | None = None, context: StepExecutionContext = None) -> FrameContext:
        """
        Write the current frame to the configured Excel workbook.

        Args:
            data:
                Frame context whose `df` is collected and written to disk.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            The same `data` frame context passed in, unchanged. Writing the
            Excel file to disk is a side effect of this call.
        """
        self.io_manager.write(data.df, table_style=self.config.table_style)
        return data
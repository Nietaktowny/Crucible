from pathlib import Path

from pydantic import BaseModel

from crucible.io import CsvIOManager
from crucible.models import StepConfig, Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import LazyFrameInstanceGuard

import polars as pl

class WriteCsvConfig(BaseModel):
    """
    Configuration for writing a Polars frame to a CSV file.
    """

    path: Path
    separator: str = ','

class WriteCsvStep(Step):
    """
    Step that writes the current frame to a CSV file on disk.

    Delegates to [`CsvIOManager`][crucible.io.CsvIOManager], which collects the
    lazy frame and writes it out using the configured separator. The input
    frame is returned unchanged so the write acts as a side effect.
    """

    key = "write_csv"
    name = "Write CSV File"
    description = "Write data to a CSV file"
    config_model =  WriteCsvConfig

    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = CsvIOManager(self.config.path, self.config.separator)

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards ensuring the input frame is a valid LazyFrame.

        Returns:
            List containing a `LazyFrameInstanceGuard`.
        """
        return [LazyFrameInstanceGuard()]

    def execute(self, data: FrameContext | None = None, context: StepExecutionContext = None) -> FrameContext:
        """
        Write the current frame to the configured CSV path.

        Args:
            data:
                Frame context whose `df` is collected and written to disk.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            The same `data` frame context passed in, unchanged. Writing the
            CSV file to disk is a side effect of this call.
        """
        self.io_manager.write(data.df)
        return data
from pathlib import Path

from pydantic import BaseModel

from crucible.io import CsvIOManager
from crucible.models import StepConfig, Step, StepExecutionContext, FrameContext

import polars as pl

class WriteCsvConfig(BaseModel):
    path: Path
    separator: str = ','

class WriteCsvStep(Step):
    key = "write_csv"
    name = "Write CSV File"
    description = "Write data to a CSV file"
    config_model =  WriteCsvConfig
    
    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = CsvIOManager(self.config.path, self.config.separator)

    def execute(self, data: FrameContext | None = None, context: StepExecutionContext = None) -> FrameContext:
        self.io_manager.write(data.df)
        return data
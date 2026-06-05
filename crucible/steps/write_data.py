from crucible.io import (
    CsvIOManager,
    IOManagerProtocol,
    IOManager
)
from crucible.models import IOConfig, StepConfig, Step

import polars as pl

class WriteDataStep(Step):
    key = "write_data"
    name = "Write Data"
    description = "Write data to a specified destination (e.g., CSV, Excel)."
    
    def __init__(self,  config: StepConfig, io_manager: IOManager, name: str = None, description: str = None):
        super().__init__(config)
        self.io_manager = io_manager
        self.name = name
        self.description = description

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        return self.io_manager.write(data)
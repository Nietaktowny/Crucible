from crucible.io import (
    CsvIOManager,
    IOManagerProtocol,
    IOManager
)
from crucible.models import IOConfig, StepConfig, Step

import polars as pl

class ReadDataStep(Step):
    key = "read_data"
    name = "Read Data"
    description = "Read data from a specified source (e.g., CSV, Excel)."
    
    def __init__(self,  config: StepConfig, io_manager: IOManager, name: str = None, description: str = None):
        super().__init__(config)
        self.io_manager = io_manager
        self.name = name
        self.description = description

    def execute(self, data: pl.LazyFrame = None) -> pl.LazyFrame:
        return self.io_manager.read(data)
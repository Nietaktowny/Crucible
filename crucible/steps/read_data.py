from crucible.io import (
    CsvIOManager,
    IOManagerProtocol,
    IOManager
)
from crucible.models import IOConfig, StepConfig, Step

import polars as pl

class ReadDataStep(Step):
    key = "read_data"
    
    def __init__(self,  config: StepConfig, io_manager: IOManager):
        super().__init__(config)
        self.io_manager = io_manager

    def execute(self, data: pl.LazyFrame = None) -> pl.LazyFrame:
        return self.io_manager.read(data)
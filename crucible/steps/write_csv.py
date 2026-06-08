from pathlib import Path

from pydantic import BaseModel

from crucible.io import CsvIOManager
<<<<<<< HEAD
from crucible.models import StepConfig, Step, StepExecutionContext
=======
from crucible.models import StepConfig, Step
>>>>>>> origin/main

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

<<<<<<< HEAD
    def execute(self, data: pl.LazyFrame = None, context: StepExecutionContext = None) -> pl.LazyFrame:
=======
    def execute(self, data: pl.LazyFrame = None) -> pl.LazyFrame:
>>>>>>> origin/main
        self.io_manager.write(data)
        return data
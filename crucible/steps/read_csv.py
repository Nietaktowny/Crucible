from pathlib import Path

from pydantic import BaseModel

from crucible.io import CsvIOManager
from crucible.models import StepConfig, Step

import polars as pl

class ReadCsvConfig(BaseModel):
    path: Path
    separator: str = ','
    infer_types: bool = False

class ReadCsvStep(Step):
    key = "read_csv"
    name = "Read CSV File"
    description = "Read data from a CSV file"
    config_model =  ReadCsvConfig
    
    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = CsvIOManager(self.config.path, self.config.separator)

    def execute(self, data: pl.LazyFrame = None) -> pl.LazyFrame:
        return self.io_manager.read(data)
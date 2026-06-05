from pathlib import Path

from pydantic import BaseModel

from crucible.io import ExcelIOManager
from crucible.models import StepConfig, Step

import polars as pl

class ReadExcelConfig(BaseModel):
    path: Path
    sheet: str | None = None

class ReadExcelStep(Step):
    key = "read_excel"
    name = "Read Excel File"
    description = "Read data from a Excel workbook."
    config_model = ReadExcelConfig
    
    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = ExcelIOManager(self.config.path, self.config.sheet)

    def execute(self, data: pl.LazyFrame = None) -> pl.LazyFrame:
        return self.io_manager.read(data)
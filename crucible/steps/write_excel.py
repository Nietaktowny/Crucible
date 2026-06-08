from pathlib import Path

from pydantic import BaseModel

from crucible.io import ExcelIOManager
<<<<<<< HEAD
from crucible.models import StepConfig, Step, StepExecutionContext
=======
from crucible.models import StepConfig, Step
>>>>>>> origin/main

import polars as pl

class WriteExcelConfig(BaseModel):
    path: Path
    sheet: str | None = None

class WriteExcelStep(Step):
    key = "write_excel"
    name = "Write Excel File"
    description = "Write data to a Excel workbook."
    config_model = WriteExcelConfig
    
    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = ExcelIOManager(self.config.path, self.config.sheet)

<<<<<<< HEAD
    def execute(self, data: pl.LazyFrame = None, context: StepExecutionContext = None) -> pl.LazyFrame:
=======
    def execute(self, data: pl.LazyFrame = None) -> pl.LazyFrame:
>>>>>>> origin/main
        self.io_manager.write(data)
        return data
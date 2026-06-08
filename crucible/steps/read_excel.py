from pathlib import Path

from pydantic import BaseModel

from crucible.io import ExcelIOManager
<<<<<<< HEAD
from crucible.models import StepConfig, Step, StepExecutionContext
=======
from crucible.models import StepConfig, Step
>>>>>>> origin/main

import polars as pl

class ReadExcelConfig(BaseModel):
    path: Path
    sheet: str | None = None
<<<<<<< HEAD
    context_store: bool = False
    context_key: str | None = None
=======
>>>>>>> origin/main

class ReadExcelStep(Step):
    key = "read_excel"
    name = "Read Excel File"
    description = "Read data from a Excel workbook."
    config_model = ReadExcelConfig
    
    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = ExcelIOManager(self.config.path, self.config.sheet)

<<<<<<< HEAD
    def execute(self, data: pl.LazyFrame = None, context: StepExecutionContext = None) -> pl.LazyFrame:
        df =  self.io_manager.read()
        if context is not None and self.config.context_store is True:
            context.extra_inputs[self.config.context_key] = df
        return df if data is None else data
=======
    def execute(self, data: pl.LazyFrame = None) -> pl.LazyFrame:
        return self.io_manager.read(data)
>>>>>>> origin/main

from pathlib import Path

from pydantic import BaseModel

from crucible.io import ExcelIOManager
from crucible.models import StepConfig, Step, StepExecutionContext

import polars as pl

class ReadExcelConfig(BaseModel):
    path: Path
    sheet: str | None = None
    context_store: bool = False
    context_key: str | None = None

class ReadExcelStep(Step):
    key = "read_excel"
    name = "Read Excel File"
    description = "Read data from a Excel workbook."
    config_model = ReadExcelConfig
    
    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = ExcelIOManager(self.config.path, self.config.sheet)

    def execute(self, data: pl.LazyFrame = None, context: StepExecutionContext = None) -> pl.LazyFrame:
        df =  self.io_manager.read()
        if context is not None and self.config.context_store is True:
            context.extra_inputs[self.config.context_key] = df
        return df if data is None else data
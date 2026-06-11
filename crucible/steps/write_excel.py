from pathlib import Path

from pydantic import BaseModel

from crucible.io import ExcelIOManager
from crucible.models import StepConfig, Step, StepExecutionContext, FrameContext, StepGuardProtocol

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

    def guards(self) -> list[StepGuardProtocol]:
        return []

    def execute(self, data: FrameContext | None = None, context: StepExecutionContext = None) -> FrameContext:
        self.io_manager.write(data.df)
        return data
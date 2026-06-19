from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from crucible.io import ExcelIOManager
from crucible.errors import MissingFileGuard
from crucible.models import StepConfig, Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.schema import build_schema

import polars as pl

class ReadExcelConfig(BaseModel):
    path: Path = Field(
        description="Path to the Excel file to read",
        json_schema_extra=build_schema(
            type_='file-path',
            source='filesystem',
            editor='file-picker'
        )
    )
    sheet: str | None = Field(
        default=None,
        description="Excel sheet to load data from",
        json_schema_extra=build_schema(
            editor='text'
        )
    )
    context_store: bool = Field(
        default=False,
        description="Store in context",
        json_schema_extra=build_schema(
            editor='checkbox'
        )
    )
    context_key: str | None = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique key to identify frame in context store"
    )
    columns: list[ColumnName] | None = Field(
        default=None,
        description="List of columns to load. If not specified all columns will be loaded.",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            editor='column-multiselect'
        )
    )

class ReadExcelStep(Step):
    key = "read_excel"
    name = "Read Excel File"
    description = "Read data from a Excel workbook."
    config_model = ReadExcelConfig
    
    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = ExcelIOManager(self.config.path, self.config.sheet)

    def guards(self) -> list[StepGuardProtocol]:
        return [MissingFileGuard(self.config.path)]

    def execute(self, data: FrameContext | None = None, context: StepExecutionContext = None) -> FrameContext:
        df =  self.io_manager.read(columns=self.config.columns)
        frame_context = FrameContext(df=df)
        if context is not None and self.config.context_store is True:
            context.extra_inputs[self.config.context_key] = frame_context
        return frame_context if data is None else data

from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from crucible.io import CsvIOManager
from crucible.models import StepConfig, Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingFileGuard
from crucible.schema import build_schema

import polars as pl

class ReadCsvConfig(BaseModel):
    path: Path = Field(
        description="Path to the CSV file to read",
        json_schema_extra=build_schema(
            type_='file-path',
            source='filesystem',
            editor='file-picker'
        )
    )
    separator: str = Field(
        default=',',
        description="CSV separator to use",
        json_schema_extra=build_schema(
            editor='text'
        )
    )
    infer_types: bool = Field(
        default=False,
        description="Auto infer column types",
        json_schema_extra=build_schema(
            editor='checkbox'
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

class ReadCsvStep(Step):
    key = "read_csv"
    name = "Read CSV File"
    description = "Read data from a CSV file"
    config_model =  ReadCsvConfig
    
    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = CsvIOManager(self.config.path, self.config.separator)

    def guards(self) -> list[StepGuardProtocol]:
        return [MissingFileGuard(self.config.path)]

    def execute(self, data: FrameContext | None = None, context: StepExecutionContext = None) -> FrameContext:
        df =  self.io_manager.read()
        frame_context = FrameContext(df=df)
        if context is not None and self.config.context_store is True:
            context.extra_inputs[self.config.context_key] = frame_context
        return frame_context if data is None else data

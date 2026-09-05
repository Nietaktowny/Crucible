from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from crucible.io import ExcelIOManager
from crucible.errors import MissingFileGuard
from crucible.models import StepConfig, Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.schema import build_schema

import polars as pl

class ReadExcelConfig(BaseModel):
    """
    Configuration for reading an Excel workbook into a Polars frame.

    When `sheet` is left as `None`, the first sheet in the workbook is read.
    When `context_store` is enabled, the resulting frame is additionally
    stored in the execution context under `context_key`.
    """

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
            editor='select',
            source='sheets'
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
    """
    Step that reads an Excel workbook into a new frame.

    Delegates to [`ExcelIOManager`][crucible.io.ExcelIOManager], which reads
    the workbook eagerly (Excel has no native lazy reader) and converts it to
    a `LazyFrame`. If a `data` frame context already exists upstream, it is
    passed through unchanged and the read frame is only exposed through the
    execution context (used as a secondary/join source); otherwise the read
    frame becomes the step's primary output.
    """

    key = "read_excel"
    name = "Read Excel File"
    description = "Read data from a Excel workbook."
    config_model = ReadExcelConfig

    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = ExcelIOManager(self.config.path, self.config.sheet)

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards ensuring the configured Excel file exists.

        Returns:
            List containing a `MissingFileGuard` for the configured path.
        """
        return [MissingFileGuard(self.config.path)]

    def execute(self, data: FrameContext | None = None, context: StepExecutionContext = None) -> FrameContext:
        """
        Read the configured Excel workbook into a new frame context.

        Args:
            data:
                Optional existing frame context. When provided, it is
                returned as-is and the newly read frame is only exposed via
                `context.extra_inputs`.

            context:
                Optional execution context. When `context_store` is enabled,
                the newly read frame context is stored in
                `context.extra_inputs` under `context_key`.

        Returns:
            A new `FrameContext` wrapping the read Excel data (optionally
            limited to `columns`) when `data` is `None`, otherwise the
            original `data` unchanged.
        """
        df =  self.io_manager.read(columns=self.config.columns)
        frame_context = FrameContext(df=df)
        if context is not None and self.config.context_store is True:
            context.extra_inputs[self.config.context_key] = frame_context
        return frame_context if data is None else data

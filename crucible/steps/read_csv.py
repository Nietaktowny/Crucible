from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from crucible.io import CsvIOManager
from crucible.models import StepConfig, Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingFileGuard
from crucible.schema import build_schema

import polars as pl

class ReadCsvConfig(BaseModel):
    """
    Configuration for reading a CSV file into a Polars frame.

    When `context_store` is enabled, the resulting frame is additionally
    stored in the execution context under `context_key`, which defaults to a
    freshly generated UUID when not explicitly set.
    """

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
    """
    Step that reads a CSV file into a new frame.

    Delegates to [`CsvIOManager`][crucible.io.CsvIOManager], which reads the
    file lazily via `polars.scan_csv`. If a `data` frame context already
    exists upstream, it is passed through unchanged and the CSV is only read
    into the execution context (used as a secondary/join source); otherwise
    the CSV becomes the step's primary output.
    """

    key = "read_csv"
    name = "Read CSV File"
    description = "Read data from a CSV file"
    config_model =  ReadCsvConfig

    def __init__(self,  config: StepConfig):
        super().__init__(config)
        self.io_manager = CsvIOManager(self.config.path, self.config.separator)

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards ensuring the configured CSV file exists.

        Returns:
            List containing a `MissingFileGuard` for the configured path.
        """
        return [MissingFileGuard(self.config.path)]

    def execute(self, data: FrameContext | None = None, context: StepExecutionContext = None) -> FrameContext:
        """
        Read the configured CSV file into a new frame context.

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
            A new `FrameContext` wrapping the lazily-read CSV data when `data`
            is `None`, otherwise the original `data` unchanged.
        """
        df =  self.io_manager.read()
        frame_context = FrameContext(df=df)
        if context is not None and self.config.context_store is True:
            context.extra_inputs[self.config.context_key] = frame_context
        return frame_context if data is None else data

from pathlib import Path
from uuid import uuid4

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import StepConfig, Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingFileGuard
from crucible.schema import build_schema

class ReadFolderCsvConfig(BaseModel):
    """
    Configuration for reading and concatenating multiple CSV files from a
    folder into a single Polars frame.

    Files are matched against `pattern` (optionally recursively) and
    concatenated using `how="diagonal_relaxed"`, so files with mismatched or
    missing columns are still combined rather than raising an error. When
    `add_source_file` is enabled, a column named `source_column` records the
    originating file name for each row.
    """

    path: Path = Field(
        description="Path to the folder with CSV files to read",
        json_schema_extra=build_schema(
            type_='file-path',
            source='filesystem',
            editor='folder-picker'
        )
    )
    pattern: str = "*.csv"
    separator: str = ","
    infer_types: bool = False
    recursive: bool = False

    add_source_file: bool = True
    source_column: str = "source_file"

    context_store: bool = False
    context_key: str = str(uuid4())
    
class ReadFolderCsvStep(Step):
    """
    Step that reads and concatenates every matching CSV file in a folder.

    Globs the configured folder for files matching `pattern` (recursively
    when `recursive` is set), reads each one lazily with `polars.scan_csv`,
    optionally tags rows with their source file name, and concatenates the
    results diagonally into a single frame. Raises `FileNotFoundError` if no
    files match.
    """

    key = "read_folder_csv"
    name = "Read CSV Folder"
    description = "Read and concatenate CSV files from a folder."
    config_model = ReadFolderCsvConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards ensuring the configured folder exists.

        Returns:
            List containing a `MissingFileGuard` for the configured path.
        """
        return [MissingFileGuard(self.config.path)]

    def execute(
        self,
        data: FrameContext | None = None,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """
        Read and concatenate all matching CSV files in the configured folder.

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
            A new `FrameContext` wrapping the concatenated CSV data when
            `data` is `None`, otherwise the original `data` unchanged.

        Raises:
            FileNotFoundError:
                If no files match `pattern` inside the configured folder.
        """

        glob_method = (
            self.config.path.rglob
            if self.config.recursive
            else self.config.path.glob
        )

        files = sorted(glob_method(self.config.pattern))

        if not files:
            raise FileNotFoundError(
                f"No files matching '{self.config.pattern}' found in '{self.config.path}'."
            )

        frames = []

        for file in files:
            df = pl.scan_csv(
                file,
                separator=self.config.separator,
                infer_schema=self.config.infer_types
            )

            if self.config.add_source_file:
                df = df.with_columns(
                    pl.lit(file.name).alias(
                        self.config.source_column
                    )
                )

            frames.append(df)

        result = pl.concat(
            frames,
            how="diagonal_relaxed",
        )

        frame_context = FrameContext(df=result)

        if context is not None and self.config.context_store:
            context.extra_inputs[self.config.context_key] = frame_context

        return frame_context if data is None else data
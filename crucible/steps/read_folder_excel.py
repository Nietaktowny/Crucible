from pathlib import Path

import polars as pl
from pydantic import BaseModel, Field

from crucible.io import ExcelIOManager
from crucible.models import StepConfig, Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingFileGuard
from crucible.schema import build_schema

class ReadFolderExcelConfig(BaseModel):
    """
    Configuration for reading and concatenating multiple Excel workbooks from
    a folder into a single Polars frame.

    Files are matched against `pattern` (optionally recursively) and
    concatenated using `how="diagonal_relaxed"`, so files with mismatched or
    missing columns are still combined rather than raising an error. Files
    that fail to read (e.g. corrupted workbooks) are silently skipped. When
    `add_source_file`/`add_source_path` are enabled, extra columns record the
    originating file name/path for each row.
    """

    path: Path = Field(
        description="Path to the folder with Excel files to read",
        json_schema_extra=build_schema(
            type_='file-path',
            source='filesystem',
            editor='folder-picker'
        )
    )
    pattern: str = "*.xlsx"
    sheet: str | None = None
    recursive: bool = False

    add_source_file: bool = True
    source_column: str = "source_file"

    add_source_path: bool = False
    source_path_column: str = "source_path"

    context_store: bool = False
    context_key: str | None = None
    
    columns: list[ColumnName] | None = None


class ReadFolderExcelStep(Step):
    """
    Step that reads and concatenates every matching Excel workbook in a
    folder.

    Globs the configured folder for files matching `pattern` (recursively
    when `recursive` is set), reads each one with `ExcelIOManager`, skips any
    file that raises while reading, optionally tags rows with their source
    file name and/or path, and concatenates the results diagonally into a
    single frame. Raises `FileNotFoundError` if no files match the pattern.
    """

    key = "read_folder_excel"
    name = "Read Excel Folder"
    description = "Read and concatenate Excel files from a folder."
    config_model = ReadFolderExcelConfig

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
        Read and concatenate all matching Excel workbooks in the configured
        folder.

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
            A new `FrameContext` wrapping the concatenated Excel data when
            `data` is `None`, otherwise the original `data` unchanged.

        Raises:
            FileNotFoundError:
                If no files match `pattern` inside the configured folder.
        """
        glob_method = self.config.path.rglob if self.config.recursive else self.config.path.glob
        files = sorted(glob_method(self.config.pattern))

        if not files:
            raise FileNotFoundError(
                f"No Excel files matching '{self.config.pattern}' found in '{self.config.path}'."
            )

        frames: list[pl.LazyFrame] = []

        for file in files:
            try:
                io_manager = ExcelIOManager(file, self.config.sheet)
                frame = io_manager.read(columns=self.config.columns)
            except Exception as e:
                continue

            if self.config.add_source_file:
                frame = frame.with_columns(
                    pl.lit(file.name).alias(self.config.source_column)
                )

            if self.config.add_source_path:
                frame = frame.with_columns(
                    pl.lit(str(file)).alias(self.config.source_path_column)
                )

            frames.append(frame)

        result = pl.concat(frames, how="diagonal_relaxed")

        frame_context = FrameContext(df=result)

        if context is not None and self.config.context_store is True:
            context.extra_inputs[self.config.context_key] = frame_context

        return frame_context if data is None else data
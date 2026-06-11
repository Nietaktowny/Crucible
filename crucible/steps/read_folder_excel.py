from pathlib import Path

import polars as pl
from pydantic import BaseModel

from crucible.io import ExcelIOManager
from crucible.models import StepConfig, Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingFileGuard


class ReadFolderExcelConfig(BaseModel):
    path: Path
    pattern: str = "*.xlsx"
    sheet: str | None = None
    recursive: bool = False

    add_source_file: bool = True
    source_column: str = "source_file"

    add_source_path: bool = False
    source_path_column: str = "source_path"

    context_store: bool = False
    context_key: str | None = None


class ReadFolderExcelStep(Step):
    key = "read_folder_excel"
    name = "Read Excel Folder"
    description = "Read and concatenate Excel files from a folder."
    config_model = ReadFolderExcelConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [MissingFileGuard(self.config.path)]

    def execute(
        self,
        data: FrameContext | None = None,
        context: StepExecutionContext = None,
    ) -> FrameContext:
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
                frame = io_manager.read()
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

        result = pl.concat(frames, how="vertical")

        frame_context = FrameContext(df=result)

        if context is not None and self.config.context_store is True:
            context.extra_inputs[self.config.context_key] = frame_context

        return frame_context if data is None else data
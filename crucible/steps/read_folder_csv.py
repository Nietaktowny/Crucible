from pathlib import Path
from uuid import uuid4

import polars as pl
from pydantic import BaseModel

from crucible.models import StepConfig, Step, StepExecutionContext


class ReadFolderCsvConfig(BaseModel):
    path: Path
    pattern: str = "*.csv"
    separator: str = ","
    infer_types: bool = False
    recursive: bool = False

    add_source_file: bool = True
    source_column: str = "source_file"

    context_store: bool = False
    context_key: str = str(uuid4())
    
class ReadFolderCsvStep(Step):
    key = "read_folder_csv"
    name = "Read CSV Folder"
    description = "Read and concatenate CSV files from a folder."
    config_model = ReadFolderCsvConfig

    def execute(
        self,
        data: pl.LazyFrame = None,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:

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
            how="diagonal",
        )

        if context is not None and self.config.context_store:
            context.extra_inputs[self.config.context_key] = result

        return result if data is None else data
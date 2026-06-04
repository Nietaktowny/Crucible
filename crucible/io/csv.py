from pathlib import Path

import polars as pl

from crucible.io._base import IOManager
from crucible.models import IOConfig

class CsvIOManager(IOManager):
    kind = "csv"

    def __init__(self, io_config: IOConfig):
        self.io_config = io_config
        self.separator = getattr(io_config, "separator", ",")

    def read(self, data: None) -> pl.LazyFrame:
        return pl.scan_csv(self.io_config.path, separator=self.separator, infer_schema=False)

    def write(self, data: pl.LazyFrame) -> int:
        df = data.collect()
        self.io_config.path.parent.mkdir(parents=True, exist_ok=True)
        df.write_csv(self.io_config.path, separator=self.separator)
        return len(df)
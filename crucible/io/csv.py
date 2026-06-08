from pathlib import Path

import polars as pl

from crucible.io._base import IOManager

class CsvIOManager(IOManager):
    kind = "csv"

    def __init__(self, path: Path, separator: str = ',', infer_types: bool = False):
        self.path = path
        self.separator =  separator
        self.infer_types = infer_types
        
    def read(self) -> pl.LazyFrame:
        return pl.scan_csv(self.path, separator=self.separator, infer_schema=self.infer_types)
    def write(self, data: pl.LazyFrame) -> int:
        df = data.collect()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        df.write_csv(self.path, separator=self.separator)
        return len(df)
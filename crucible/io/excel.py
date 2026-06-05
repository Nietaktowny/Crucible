from pathlib import Path

import polars as pl

from crucible.io._base import IOManager
from crucible.models import IOConfig

class ExcelIOManager(IOManager):
    kind = "excel"

    def __init__(self, io_config: IOConfig):
        self.io_config = io_config
        self.sheet = getattr(io_config, "sheet")

    def read(self, data: None) -> pl.LazyFrame:
        if self.sheet is not None:
            return pl.read_excel(self.io_config.path, sheet_name=self.sheet, engine='calamine').lazy()
        return pl.read_excel(self.io_config.path, engine='calamine', sheet_id=1).lazy()

    def write(self, data: pl.LazyFrame) -> int:
        df = data.collect()
        self.io_config.path.parent.mkdir(parents=True, exist_ok=True)
        if self.sheet is not None:
            df.write_excel(self.io_config.path, sheet_name=self.sheet, table_style="Table Style Light 16",)
        df.write_excel(self.io_config.path, table_style="Table Style Light 16",)
        return len(df)
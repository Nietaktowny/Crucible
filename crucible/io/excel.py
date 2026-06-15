from pathlib import Path

import polars as pl

from crucible.io._base import IOManager

class ExcelIOManager(IOManager):
    kind = "excel"

    def __init__(self, path: Path, sheet: str | None = None):
        self.path = path
        self.sheet = sheet
        
    def read(self, columns: list[str] | None = None) -> pl.LazyFrame:
        if self.sheet is not None:
            return pl.read_excel(self.path, sheet_name=self.sheet, engine='calamine', columns=columns).lazy()
        return pl.read_excel(self.path, engine='calamine', sheet_id=1).lazy()

    def write(self, data: pl.LazyFrame,
              table_style: str = "Table Style Medium 1") -> int:
        df = data.collect()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.sheet is not None:
            df.write_excel(self.path, worksheet=self.sheet, table_style=table_style)
        else:
            df.write_excel(self.path, table_style=table_style)
        return len(df)
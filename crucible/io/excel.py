from pathlib import Path

import polars as pl

from crucible.io._base import IOManager

class ExcelIOManager(IOManager):
    """IO manager used for working with Excel files.
    """
    
    kind = "excel"

    def __init__(self, path: Path, sheet: str | None = None):
        self.path = path
        self.sheet = sheet
        
    def read(self, columns: list[str] | None = None) -> pl.LazyFrame:
        """Read Excel file into `pl.LazyFrame`.
        
        `polars` doesn't support reading Excel files lazily,
        that's why it's read into materialized `polars.DataFrame`
        and then converted to `polars.LazyFrame`.
        As Excel files have rows limits, and don't support
        containing large amounts of rows, it shouldn't be critical performance problem,
        but it should be taken into consideration.   
        
        The `columns` variable can be passed to limit
        columns loaded.
        
        If self.sheet variable is None, sheet with
        first index is loaded.

        Args:
            columns (list[str] | None, optional): List of columns to read from file. If None, all columns will be read. Defaults to None.

        Returns:
            pl.LazyFrame: LazyFrame read from file.
        """
        if self.sheet is not None:
            return pl.read_excel(self.path, sheet_name=self.sheet, engine='calamine', columns=columns).lazy()
        return pl.read_excel(self.path, engine='calamine', sheet_id=1).lazy()

    def write(self, data: pl.LazyFrame,
              table_style: str = "Table Style Medium 1") -> int:
        """Collects `polars.LazyFrame` and writes it to Excel file.

        The self.sheet variable is used to control sheet name.
        If it's None, default name like 'Sheet1' will be used.
        
        Supports pretty formatting data as Excel table
        using specified style. Refer to styles available
        in Excel for their names.
        
        Args:
            data (pl.LazyFrame): Data to save.

        Returns:
            int: Number of rows saved.
        """
        df = data.collect()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.sheet is not None:
            df.write_excel(self.path, worksheet=self.sheet, table_style=table_style)
        else:
            df.write_excel(self.path, table_style=table_style)
        return len(df)
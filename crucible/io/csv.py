from pathlib import Path

import polars as pl

from crucible.io._base import IOManager

class CsvIOManager(IOManager):
    """IO manager used for working with CSV files.
    """
    
    kind = "csv"

    def __init__(self, path: Path, separator: str = ',', infer_types: bool = False):
        self.path = path
        self.separator =  separator
        self.infer_types = infer_types
        
    def read(self, columns: list[str] | None = None) -> pl.LazyFrame:
        """Read CSV file into `pl.LazyFrame`.
        
        Internally the CSV file is read lazily using `polars.scan_csv` function.
        That's why `columns` argument is actually ignored, and added here only for uniform
        shape of function between other IO managers.

        Args:
            columns (list[str] | None, optional): Ignored. Defaults to None.

        Returns:
            pl.LazyFrame: LazyFrame read from file.
        """
        return pl.scan_csv(self.path, separator=self.separator, infer_schema=self.infer_types)
    
    def write(self, data: pl.LazyFrame) -> int:
        """Collects `polars.LazyFrame` and writes it to CSV file.

        Separator is configured using the separator variable.
        
        Args:
            data (pl.LazyFrame): Data to save.

        Returns:
            int: Number of rows saved.
        """
        df = data.collect()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        df.write_csv(self.path, separator=self.separator)
        return len(df)
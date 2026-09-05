"""
IO managers used by read/write steps to move data in and out of Polars
frames. Each manager (`CsvIOManager`, `ExcelIOManager`) implements the
`IOManagerProtocol` `read`/`write` interface for one file format, so step
implementations don't need to know format-specific details.
"""

from crucible.io._base import IOManager, IOManagerProtocol
from crucible.io.csv import CsvIOManager
from crucible.io.excel import ExcelIOManager

__all__ = [
    "CsvIOManager",
    "IOManager",
    "IOManagerProtocol",
    "ExcelIOManager"
]
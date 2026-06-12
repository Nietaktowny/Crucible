from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

import polars as pl

from crucible.models import FrameContext
from crucible.errors._errors import (
    ColumnNotFoundError,
    ColumnTypeMismatchError
)

class StepGuardBase(ABC):
    
    @abstractmethod
    def check(self, data: FrameContext) -> None:
        """Check dataframe and raise error if guard fails"""

class MissingColumnsGuard(StepGuardBase):    
    def __init__(self, columns: list[str]) -> None:
        super().__init__()
        self.columns = columns

    def check(self, data: FrameContext) -> None:
        missing = [column for column in self.columns if column not in data.schema.keys()]
        if missing:
            raise ColumnNotFoundError(f"Column or columns not found in data schema: {missing}. Available columns: {list(data.schema.keys())}")
class ColumnsTypeGuard(StepGuardBase):
    def __init__(self, schema: dict[str, str | Sequence[str]]) -> None:
        super().__init__()
        self.expected_schema = schema

    def check(self, data: FrameContext) -> None:
        mismatches: dict[str, dict[str, object]] = {}

        for column, expected_type in self.expected_schema.items():
            expected_type = str(expected_type).lower()
            actual_type = data.schema.get(column)

            if isinstance(expected_type, str):
                expected_types = [expected_type]
            else:
                expected_types = list(expected_type)

            if str(actual_type).lower() not in expected_types:
                mismatches[column] = {
                    "actual": actual_type,
                    "expected": expected_types,
                }

        if mismatches:
            raise ColumnTypeMismatchError(
                f"Columns with different type than expected found: {mismatches}"
            )
            
class MissingFileGuard(StepGuardBase):    
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

    def check(self, data: FrameContext) -> None:
        if not self.path.exists():
            if self.path.is_dir():
                raise FileNotFoundError(f"Directory under path '{self.path.absolute()}' doesn't exist!")
            else:
                raise FileNotFoundError(f"File under path '{self.path.absolute()}' doesn't exist!")            
class LazyFrameInstanceGuard(StepGuardBase):    
    def __init__(self) -> None:
        super().__init__()

    def check(self, data: FrameContext) -> None:
        if not isinstance(data.df, pl.LazyFrame):
            raise ValueError(f"Data passed between steps has to be of LazyFrame type. Passed: '{type(data.df)}'")
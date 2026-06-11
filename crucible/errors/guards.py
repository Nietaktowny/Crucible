from functools import wraps
from typing import Callable
from abc import ABC, abstractmethod

import polars as pl
from pydantic import BaseModel

from crucible.models import FrameContext
from crucible.errors._errors import (
    ColumnNotFoundError,
    ColumnTypeMismatchError
)

class StepGuardBase(ABC):
    
    @abstractmethod
    def check(self, frame: FrameContext) -> None:
        """Check dataframe and raise error if guard fails"""

class MissingColumnsGuard(StepGuardBase):    
    def __init__(self, columns: list[str]) -> None:
        super().__init__()
        self.columns = columns

    def check(self, frame: FrameContext) -> None:
        missing = [column for column in self.columns if column not in frame.schema.keys()]
        if missing:
            raise ColumnNotFoundError(f"Column or columns not found in data schema: {missing}. Available columns: {frame.schema.keys()}")

class ColumnsTypeGuard(StepGuardBase):    
    def __init__(self, schema: dict[str, str]) -> None:
        super().__init__()
        self.expected_schema = schema

    def check(self, frame: FrameContext) -> None:
        mismatch = {}
        for column, expected_type in self.expected_schema:
            actual_type = frame.schema.get(column, None)
            if actual_type != expected_type:
                mismatch.update({expected_type: actual_type})
        if mismatch:
            raise ColumnTypeMismatchError(f"Columns with different type than expected found. Actual to expected comparison: {mismatch}")

def step_guard(guards: list[StepGuardBase]) -> Callable:
    @wraps
    def _step_guard(func: Callable) -> Callable:
        @wraps
        def _execute(frame: FrameContext, *args, **kwargs) -> FrameContext:
            for guard in guards:
                guard.check(frame)
            
            return func(frame, *args, **kwargs)
        return _execute
    return _step_guard
        
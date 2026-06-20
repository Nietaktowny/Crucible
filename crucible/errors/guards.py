from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

import polars as pl

from crucible.errors._errors import (
    ColumnNotFoundError,
    ColumnTypeMismatchError,
)
from crucible.models import FrameContext


class StepGuardBase(ABC):
    """
    Base class for runtime step guards.

    Guards validate assumptions that must be true before or during step
    execution. They are used to fail early with a clear error when the input
    frame, schema, file path, or expected column types are invalid.

    Subclasses implement [`check`][crucible.guards.StepGuardBase.check] and
    raise an exception when validation fails.
    """

    @abstractmethod
    def check(self, data: FrameContext) -> None:
        """
        Validate step input.

        Args:
            data:
                Current frame context passed to the step.

        Raises:
            Exception:
                Concrete guard implementations raise specific exceptions when
                validation fails.
        """


class MissingColumnsGuard(StepGuardBase):
    """
    Guard that validates whether required columns exist in a frame schema.

    This guard is useful for transformations that depend on specific input
    columns, such as selecting, renaming, filtering, sorting, or changing column
    types.
    """

    def __init__(self, columns: list[str]) -> None:
        """
        Initialize the guard.

        Args:
            columns:
                Required column names.
        """
        super().__init__()
        self.columns = columns

    def check(self, data: FrameContext) -> None:
        """
        Check that all required columns exist in the frame schema.

        Args:
            data:
                Frame context containing the current schema.

        Raises:
            ColumnNotFoundError:
                If at least one required column is missing.
        """
        if data is not None and data.schema is not None:
            missing = [
                column
                for column in self.columns
                if column not in data.schema.keys()
            ]

            if missing:
                raise ColumnNotFoundError(
                    "Column or columns not found in data schema: "
                    f"{missing}. Available columns: {list(data.schema.keys())}"
                )


class ColumnsTypeGuard(StepGuardBase):
    """
    Guard that validates expected column data types.

    The expected schema maps column names to either one accepted type or a
    sequence of accepted types. Type names are normalized to lowercase strings
    before comparison.

    Example:
        ```python
        guard = ColumnsTypeGuard(
            {
                "Date": ["date", "datetime"],
                "Amount": "float64",
            }
        )
        ```
    """

    def __init__(self, schema: dict[str, str | Sequence[str]]) -> None:
        """
        Initialize the guard.

        Args:
            schema:
                Mapping from column name to expected type or accepted types.
        """
        super().__init__()
        self.expected_schema = schema

    def check(self, data: FrameContext) -> None:
        """
        Check that configured columns have expected data types.

        Args:
            data:
                Frame context containing the current schema.

        Raises:
            ColumnTypeMismatchError:
                If at least one column has a type different from the expected
                type set.
        """
        mismatches: dict[str, dict[str, object]] = {}

        for column, expected_type in self.expected_schema.items():
            actual_type = str(data.schema.get(column)).lower().strip()

            if isinstance(expected_type, str):
                expected_types = [str(expected_type).lower().strip()]
            else:
                expected_types = [
                    str(expected).lower().strip()
                    for expected in list(expected_type)
                ]

            if actual_type not in expected_types:
                mismatches[column] = {
                    "actual": actual_type,
                    "expected": expected_types,
                }

        if mismatches:
            raise ColumnTypeMismatchError(
                "Columns with different type than expected found: "
                f"{mismatches}"
            )


class MissingFileGuard(StepGuardBase):
    """
    Guard that validates whether a configured file-system path exists.

    This guard is mainly used by input steps before attempting to read files or
    folders.
    """

    def __init__(self, path: Path) -> None:
        """
        Initialize the guard.

        Args:
            path:
                File or directory path that must exist.
        """
        super().__init__()
        self.path = path

    def check(self, data: FrameContext) -> None:
        """
        Check that the configured path exists.

        Args:
            data:
                Unused frame context. Present for compatibility with the guard
                interface.

        Raises:
            FileNotFoundError:
                If the configured path does not exist.
        """
        if not self.path.exists():
            if self.path.is_dir():
                raise FileNotFoundError(
                    f"Directory under path '{self.path.absolute()}' "
                    "doesn't exist!"
                )

            raise FileNotFoundError(
                f"File under path '{self.path.absolute()}' doesn't exist!"
            )


class LazyFrameInstanceGuard(StepGuardBase):
    """
    Guard that validates whether step input contains a Polars LazyFrame.

    This guard protects transformations that require lazy Polars execution and
    cannot operate on missing data or an unexpected frame type.
    """

    def __init__(self) -> None:
        """Initialize the guard."""
        super().__init__()

    def check(self, data: FrameContext) -> None:
        """
        Check that the frame context exists and contains a Polars LazyFrame.

        Args:
            data:
                Frame context expected to contain a `polars.LazyFrame`.

        Raises:
            ValueError:
                If the frame context is missing or does not contain a lazy
                frame.
        """
        if data is None:
            raise ValueError("FrameContext for this step cannot be null.")

        if not isinstance(data.df, pl.LazyFrame):
            raise ValueError(
                "Data expected by step has to be of LazyFrame type. "
                f"Passed: '{type(data.df)}'"
            )
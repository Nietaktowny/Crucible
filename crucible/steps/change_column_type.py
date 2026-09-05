from typing import Literal

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import (
    MissingColumnsGuard,
    LazyFrameInstanceGuard
)
import polars as pl
from pydantic import BaseModel, Field

POLARS_TYPES = {
    "string": pl.String,
    "text": pl.String,
    "int8": pl.Int8,
    "int16": pl.Int16,
    "int32": pl.Int32,
    "int64": pl.Int64,
    "uint8": pl.UInt8,
    "uint16": pl.UInt16,
    "uint32": pl.UInt32,
    "uint64": pl.UInt64,
    "float32": pl.Float32,
    "float64": pl.Float64,
    "boolean": pl.Boolean,
    "date": pl.Date,
    "datetime": pl.Datetime,
    "time": pl.Time,
}


class ChangeColumnTypeConfig(BaseModel):
    """
    Configuration for [`ChangeColumnTypeStep`][crucible.steps.change_column_type.ChangeColumnTypeStep].

    Maps column names to one of the type names in this module's
    `POLARS_TYPES` lookup; both `"string"` and `"text"` resolve to
    `polars.String`.
    """

    column_types: dict[ColumnName, Literal[
        "string",
        "text",
        "int8",
        "int16",
        "int32",
        "int64",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
        "float32",
        "float64",
        "boolean",
        "date",
        "datetime",
        "time",
    ]] = Field(
        description="Mapping from column name to new type.",
    )

class ChangeColumnTypeStep(Step):
    """
    Step that casts one or more columns to a different data type.

    For each configured column, the requested type name is resolved through
    this module's `POLARS_TYPES` lookup and applied with Polars' `cast`
    expression.
    """

    key = "change_column_type"
    name = "Change Column Type"
    description = "Change the data type of one or more columns."
    config_model = ChangeColumnTypeConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before casting columns.

        Returns:
            A [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard]
            ensuring the input is a Polars `LazyFrame`, and a
            [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard]
            ensuring every column named in `column_types` exists in the frame
            schema.
        """
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(self.config.column_types.keys()),
        ]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        """
        Cast the configured columns to their target Polars data types.

        Args:
            data:
                Frame context whose `df` has columns cast.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the frame with columns cast to their
            new types.
        """
        result = data.df.with_columns([
            pl.col(col).cast(POLARS_TYPES.get(dtype))
            for col, dtype in self.config.column_types.items()
        ])
        return FrameContext(df=result)
from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class DateAddConfig(BaseModel):
    """Configuration for adding or subtracting a fixed duration from a date/datetime column."""

    column: ColumnName = Field(
        description="Column with date to use as input",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )

    value: int = Field(description="Number of units to add")
    unit: Literal[
        "days",
        "hours",
        "minutes",
        "seconds",
        "milliseconds",
    ] = Field(
        default='days',
        description="Unit of date to add",
        json_schema_extra=build_schema(
            type_='literal-value',
            source='enum'
        )
    )

    output_column: ColumnName | None = Field(
        default=None,
        description="Column to save output into.",
        json_schema_extra=build_schema(
            type_='column-name',
            role='output-column'
        )
    )


class DateAddStep(Step):
    """Add a signed duration (days, hours, minutes, seconds, or milliseconds) to a date/datetime column.

    The value is added using `pl.duration`, so a negative `value` subtracts the
    duration instead. When `output_column` is not set, the source column is
    overwritten in place.
    """

    key = "date_add"
    name = "Date Add"
    description = "Add or subtract duration from a date or datetime column."
    config_model = DateAddConfig

    def guards(self) -> list[StepGuardProtocol]:
        """Guard against a non-lazy frame, a missing input column, or a wrong column type.

        Returns:
            List containing a [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard],
            a [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard] for the configured
            column, and a [`ColumnsTypeGuard`][crucible.errors.ColumnsTypeGuard] requiring it to
            be `Date` or `Datetime`.
        """
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard([self.config.column]),
            ColumnsTypeGuard({self.config.column: ["Date", "Datetime"]}),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """Add the configured duration to the source column and write it to the output column.

        Args:
            data:
                Current frame context whose `df` must contain the configured
                `column` as a `Date` or `Datetime` column.

            context:
                Unused execution context.

        Returns:
            Updated frame context with the resulting lazy frame.
        """
        output_column = self.config.output_column or self.config.column

        expression = (
            pl.col(self.config.column)
            + self._build_duration()
        ).alias(output_column)

        result = data.df.with_columns(expression)
        return FrameContext(df=result)

    def _build_duration(self) -> pl.Expr:
        match self.config.unit:
            case "days":
                return pl.duration(days=self.config.value)
            case "hours":
                return pl.duration(hours=self.config.value)
            case "minutes":
                return pl.duration(minutes=self.config.value)
            case "seconds":
                return pl.duration(seconds=self.config.value)
            case "milliseconds":
                return pl.duration(milliseconds=self.config.value)
            case _:
                raise ValueError(f"Unsupported unit: {self.config.unit}")
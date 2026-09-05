from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class ExtractDateTimePartConfig(BaseModel):
    """Configuration for extracting a single numeric component (year, month, hour, etc.) from a date/datetime/time column."""

    column: ColumnName = Field(
        description="Column to extract datetime part from",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )
    part: Literal[
        "year",
        "month",
        "day",
        "week",
        "weekday",
        "hour",
        "minute",
        "second",
    ] = Field(
        description="Part of datetime to extract",
        json_schema_extra=build_schema(
            type_='literal-value',
            editor='select',
            source='enum'
        )
    )

    output_column: ColumnName | None = Field(
        default=None,
        description="Output column. If not specified auto generated name will be used",
        json_schema_extra=build_schema(
            type_='column-name',
            role='output-column',
            editor='text'
        )
    )


class ExtractDateTimePartStep(Step):
    """Extract one numeric part (year, month, day, week, weekday, hour, minute, or second) from a date/datetime/time column.

    The part is read via the matching `Expr.dt.*` accessor (e.g. `dt.year()`,
    `dt.weekday()`); which parts are actually available depends on the source
    column's type (e.g. `hour`/`minute`/`second` are meaningless on a plain
    `Date`), but this step does not restrict `part` based on the column's
    concrete dtype beyond requiring `Date`, `Datetime`, or `Time`. When
    `output_column` is not set, the result is written to
    `"<column>_<part>"`.
    """

    key = "extract_datetime_part"
    name = "Extract Date/Time Part"
    description = "Extract a selected part from a date, datetime, or time column."
    config_model = ExtractDateTimePartConfig

    def guards(self) -> list[StepGuardProtocol]:
        """Guard against a non-lazy frame, a missing input column, or a wrong column type.

        Returns:
            List containing a [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard],
            a [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard] for the configured
            column, and a [`ColumnsTypeGuard`][crucible.errors.ColumnsTypeGuard] requiring it to
            be `Date`, `Datetime`, or `Time`.
        """
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard([self.config.column]),
            ColumnsTypeGuard({self.config.column: ["Date", "Datetime", "Time"]}),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """Extract the configured part and write it to the output column.

        Args:
            data:
                Current frame context whose `df` must contain the configured
                `column` as a `Date`, `Datetime`, or `Time` column.

            context:
                Unused execution context.

        Returns:
            Updated frame context with the resulting lazy frame.
        """
        output_column = self.config.output_column or f"{self.config.column}_{self.config.part}"

        expression = self._build_expression().alias(output_column)

        result = data.df.with_columns(expression)
        return FrameContext(df=result)

    def _build_expression(self) -> pl.Expr:
        column = pl.col(self.config.column)

        match self.config.part:
            case "year":
                return column.dt.year()
            case "month":
                return column.dt.month()
            case "day":
                return column.dt.day()
            case "week":
                return column.dt.week()
            case "weekday":
                return column.dt.weekday()
            case "hour":
                return column.dt.hour()
            case "minute":
                return column.dt.minute()
            case "second":
                return column.dt.second()
            case _:
                raise ValueError(f"Unsupported date/time part: {self.config.part}")
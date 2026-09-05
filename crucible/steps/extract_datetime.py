from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class ExtractDateTimeConfig(BaseModel):
    """Configuration for extracting the date or time component of a datetime column."""

    column: ColumnName = Field(
        description="Column to extract datetime part from",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )
    extract: Literal["date", "time"] = Field(
        description="Whether to extract date or time from datetime",
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


class ExtractDateTimeStep(Step):
    """Split a `Datetime` column into its `Date` or `Time` component using `Expr.dt.date`/`Expr.dt.time`.

    Unlike `ExtractDateTimePartStep`, the source column must already be a
    `Datetime` (not `Date` or `Time`). When `output_column` is not set, the
    result is written to `"<column>_<extract>"`.
    """

    key = "extract_date_time"
    name = "Extract Date/Time"
    description = "Extract date or time from a datetime column."
    config_model = ExtractDateTimeConfig

    def guards(self) -> list[StepGuardProtocol]:
        """Guard against a non-lazy frame, a missing input column, or a non-`Datetime` column.

        Returns:
            List containing a [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard],
            a [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard] for the configured
            column, and a [`ColumnsTypeGuard`][crucible.errors.ColumnsTypeGuard] requiring it to
            be `Datetime`.
        """
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard([self.config.column]),
            ColumnsTypeGuard({self.config.column: ["Datetime"]}),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """Extract the configured date/time component and write it to the output column.

        Args:
            data:
                Current frame context whose `df` must contain the configured
                `column` as a `Datetime` column.

            context:
                Unused execution context.

        Returns:
            Updated frame context with the resulting lazy frame.
        """
        output_column = self.config.output_column or f"{self.config.column}_{self.config.extract}"

        expression = self._build_expression().alias(output_column)

        result = data.df.with_columns(expression)
        return FrameContext(df=result)

    def _build_expression(self) -> pl.Expr:
        column = pl.col(self.config.column)

        match self.config.extract:
            case "date":
                return column.dt.date()
            case "time":
                return column.dt.time()
            case _:
                raise ValueError(f"Unsupported extraction: {self.config.extract}")
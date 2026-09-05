from datetime import date, datetime
from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class DateRangeFilterConfig(BaseModel):
    """Configuration for filtering rows to a date/datetime range.

    `start` and `end` are ISO-formatted string literals whose parsing is
    controlled by `value_type` (`date` uses `date.fromisoformat`, `datetime`
    uses `datetime.fromisoformat`).
    """

    column: ColumnName = Field(
        default=None,
        description="Column with date value used as ending point",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )

    start: str = Field(
        description="Range start",
        json_schema_extra=build_schema(
            editor='datetime-picker'
        )
    )
    end: str = Field(
        description="Range end",
        json_schema_extra=build_schema(
            editor='datetime-picker'
        )
    )

    value_type: Literal["date", "datetime"] = Field(
        default="date",
        description="What range value type to use for filtering",
        json_schema_extra=build_schema(
            type_='literal-value',
            editor='select',
            source='enum'
        )
    )
    closed: Literal["both", "left", "right", "none"] = Field(
        default="both",
        description="How to treat range ends",
        json_schema_extra=build_schema(
            type_='literal-value',
            editor='select',
            source='enum'
        )
    )


class DateRangeFilterStep(Step):
    """Keep only rows whose date/datetime column falls within `[start, end]`.

    `start` and `end` are parsed as either `date` or `datetime` literals
    (per `value_type`) and compared using `Expr.is_between`, with boundary
    inclusion controlled by `closed` (`both`, `left`, `right`, or `none`).
    """

    key = "date_range_filter"
    name = "Date Range Filter"
    description = "Filter rows where a date or datetime column is within a range."
    config_model = DateRangeFilterConfig

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
        """Parse the range bounds and filter rows to that range.

        Args:
            data:
                Current frame context whose `df` must contain the configured
                `column` as a `Date` or `Datetime` column.

            context:
                Unused execution context.

        Returns:
            Updated frame context with the filtered lazy frame.
        """
        start_value = self._parse_literal(self.config.start)
        end_value = self._parse_literal(self.config.end)

        result = data.df.filter(
            pl.col(self.config.column).is_between(
                lower_bound=start_value,
                upper_bound=end_value,
                closed=self.config.closed,
            )
        )
        return FrameContext(df=result)

    def _parse_literal(self, value: str) -> date | datetime:
        match self.config.value_type:
            case "date":
                return date.fromisoformat(value)
            case "datetime":
                return datetime.fromisoformat(value)
            case _:
                raise ValueError(f"Unsupported value_type: {self.config.value_type}")
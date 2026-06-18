from datetime import date, datetime
from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class DateRangeFilterConfig(BaseModel):
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

    start: str
    end: str

    value_type: Literal["date", "datetime"] = "date"
    closed: Literal["both", "left", "right", "none"] = "both"


class DateRangeFilterStep(Step):
    key = "date_range_filter"
    name = "Date Range Filter"
    description = "Filter rows where a date or datetime column is within a range."
    config_model = DateRangeFilterConfig

    def guards(self) -> list[StepGuardProtocol]:
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
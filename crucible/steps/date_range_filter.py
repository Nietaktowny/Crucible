from datetime import date, datetime
from typing import Literal

import polars as pl
from pydantic import BaseModel, model_validator

from crucible.models import Step, StepExecutionContext


class DateRangeFilterConfig(BaseModel):
    column: str

    start: str
    end: str

    value_type: Literal["date", "datetime"] = "date"
    closed: Literal["both", "left", "right", "none"] = "both"


class DateRangeFilterStep(Step):
    key = "date_range_filter"
    name = "Date Range Filter"
    description = "Filter rows where a date or datetime column is within a range."
    config_model = DateRangeFilterConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        start_value = self._parse_literal(self.config.start)
        end_value = self._parse_literal(self.config.end)

        return data.filter(
            pl.col(self.config.column).is_between(
                lower_bound=start_value,
                upper_bound=end_value,
                closed=self.config.closed,
            )
        )

    def _parse_literal(self, value: str) -> date | datetime:
        match self.config.value_type:
            case "date":
                return date.fromisoformat(value)
            case "datetime":
                return datetime.fromisoformat(value)
            case _:
                raise ValueError(f"Unsupported value_type: {self.config.value_type}")
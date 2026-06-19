from datetime import date

import polars as pl
from pydantic import BaseModel, Field
from typing import Literal

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class DatePeriodFilterConfig(BaseModel):
    column: ColumnName = Field(
        description="Column to filter period in",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )
    

    period: Literal[
        "current_year",
        "current_month",
        "current_day",
    ] = Field(
        description="Period to filter to",
        json_schema_extra=build_schema(
            type_='literal-value',
            editor='select',
            source='enum'
        )
    )


class DatePeriodFilterStep(Step):
    key = "date_period_filter"
    name = "Date Period Filter"
    description = "Filter rows belonging to the current year, month or day."
    config_model = DatePeriodFilterConfig

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
        today = date.today()

        match self.config.period:
            case "current_year":
                condition = (
                    pl.col(self.config.column).dt.year()
                    == today.year
                )

            case "current_month":
                condition = (
                    (pl.col(self.config.column).dt.year() == today.year)
                    &
                    (pl.col(self.config.column).dt.month() == today.month)
                )

            case "current_day":
                condition = (
                    (pl.col(self.config.column).dt.year() == today.year)
                    &
                    (pl.col(self.config.column).dt.month() == today.month)
                    &
                    (pl.col(self.config.column).dt.day() == today.day)
                )

            case _:
                raise ValueError(
                    f"Unsupported period: {self.config.period}"
                )

        result = data.df.filter(condition)
        return FrameContext(df=result)
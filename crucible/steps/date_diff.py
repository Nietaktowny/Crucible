from typing import Literal

import polars as pl
from pydantic import BaseModel, model_validator

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard


class DateDiffConfig(BaseModel):
    start_column: str | None = None
    end_column: str | None = None

    start_value: str | None = None
    end_value: str | None = None

    unit: Literal[
        "days",
        "hours",
        "minutes",
        "seconds",
        "milliseconds",
    ] = "days"

    output_column: str

    @model_validator(mode="after")
    def validate_configuration(self):
        has_start = self.start_column is not None or self.start_value is not None
        has_end = self.end_column is not None or self.end_value is not None

        if not has_start:
            raise ValueError("Either start_column or start_value must be provided.")

        if not has_end:
            raise ValueError("Either end_column or end_value must be provided.")

        if self.start_column is not None and self.start_value is not None:
            raise ValueError("Use either start_column or start_value, not both.")

        if self.end_column is not None and self.end_value is not None:
            raise ValueError("Use either end_column or end_value, not both.")

        return self


class DateDiffStep(Step):
    key = "date_diff"
    name = "Date Difference"
    description = "Calculate difference between two date or datetime values."
    config_model = DateDiffConfig

    def guards(self) -> list[StepGuardProtocol]:
        columns_to_check = {}
        if self.config.start_column:
            columns_to_check[self.config.start_column] = ["Date", "Datetime"]
        if self.config.end_column:
            columns_to_check[self.config.end_column] = ["Date", "Datetime"]
        
        guards: list[StepGuardProtocol] = []
        if columns_to_check:
            guards.extend([
                MissingColumnsGuard(list(columns_to_check.keys())),
                ColumnsTypeGuard(columns_to_check),
            ])
        return guards

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        start_expr = self._build_value_expression(
            column=self.config.start_column,
            value=self.config.start_value,
        )

        end_expr = self._build_value_expression(
            column=self.config.end_column,
            value=self.config.end_value,
        )

        duration_expr = end_expr - start_expr

        result = data.df.with_columns(
            self._convert_duration(duration_expr).alias(self.config.output_column)
        )
        return FrameContext(df=result)

    def _build_value_expression(
        self,
        column: str | None,
        value: str | None,
    ) -> pl.Expr:
        if column is not None:
            return pl.col(column)

        return pl.lit(value).str.strptime(
            dtype=pl.Datetime,
            format=None,
            strict=False,
        )

    def _convert_duration(self, expression: pl.Expr) -> pl.Expr:
        match self.config.unit:
            case "days":
                return expression.dt.total_days()
            case "hours":
                return expression.dt.total_hours()
            case "minutes":
                return expression.dt.total_minutes()
            case "seconds":
                return expression.dt.total_seconds()
            case "milliseconds":
                return expression.dt.total_milliseconds()
            case _:
                raise ValueError(f"Unsupported unit: {self.config.unit}")
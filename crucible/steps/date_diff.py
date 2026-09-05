from typing import Literal

import polars as pl
from pydantic import BaseModel, model_validator, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class DateDiffConfig(BaseModel):
    """Configuration for computing the difference between two date/datetime endpoints.

    Each endpoint (start/end) must be provided as either a column reference or a
    literal string value, never both, and never neither; this is enforced by
    `validate_configuration`.
    """

    start_column: ColumnName | None = Field(
        default=None,
        description="Column with date value used as starting point",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )
    end_column: ColumnName | None = Field(
        default=None,
        description="Column with date value used as ending point",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )

    start_value: str | None = Field(
        default=None,
        description="Value used as starting point"
    )
    end_value: str | None = Field(
        default=None,
        description="Value used as ending point"
    )

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

    output_column: ColumnName = Field(
        description="Column to save output into.",
        json_schema_extra=build_schema(
            type_='column-name',
            role='output-column'
        )
    )

    @model_validator(mode="after")
    def validate_configuration(self):
        """Ensure each endpoint has exactly one source and both endpoints are provided.

        Raises:
            ValueError: If a start or end endpoint is missing, or if both a
                column and a literal value are supplied for the same endpoint.
        """
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
    """Compute `end - start` between two date/datetime endpoints and express it in a chosen unit.

    Each endpoint is resolved either from a column or by parsing a literal
    string value with `str.strptime` (non-strict, format auto-detected), and
    the resulting duration is converted to whole days, hours, minutes,
    seconds, or milliseconds and written to `output_column`.
    """

    key = "date_diff"
    name = "Date Difference"
    description = "Calculate difference between two date or datetime values."
    config_model = DateDiffConfig

    def guards(self) -> list[StepGuardProtocol]:
        """Guard the frame and any endpoint columns that were configured.

        Only endpoints backed by a column are checked; endpoints backed by a
        literal value are skipped since there is no column to validate.

        Returns:
            Empty list when neither endpoint uses a column, otherwise a list
            containing a [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard],
            a [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard] for the
            configured endpoint columns, and a
            [`ColumnsTypeGuard`][crucible.errors.ColumnsTypeGuard] requiring them to be
            `Date` or `Datetime`.
        """
        columns_to_check = {}
        if self.config.start_column:
            columns_to_check[self.config.start_column] = ["Date", "Datetime"]
        if self.config.end_column:
            columns_to_check[self.config.end_column] = ["Date", "Datetime"]
        
        guards: list[StepGuardProtocol] = []
        if columns_to_check:
            guards.extend([
                LazyFrameInstanceGuard(),
                MissingColumnsGuard(list(columns_to_check.keys())),
                ColumnsTypeGuard(columns_to_check),
            ])
        return guards

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """Resolve both endpoints, subtract them, and write the converted duration.

        Args:
            data:
                Current frame context whose `df` must contain any configured
                endpoint columns as `Date` or `Datetime` columns.

            context:
                Unused execution context.

        Returns:
            Updated frame context with the resulting lazy frame.
        """
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
from typing import Any

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema


class FillNullsConfig(BaseModel):
    """Configuration for [`FillNullsStep`][crucible.steps.fill_nulls.FillNullsStep]."""

    columns: list[ColumnName] = Field(
        description="List of columns to replace nulls in",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )
    value: Any = Field(
        description="Value to replace nulls with",
        json_schema_extra=build_schema(
            editor='text'
        )
    )


class FillNullsStep(Step):
    """
    Step that replaces null values in one or more columns with a fixed value.

    For each configured column, applies Polars' `fill_null` expression with
    the same configured `value`, regardless of the column's data type.
    """

    key = "fill_nulls"
    name = "Fill Nulls"
    description = "Replace null values with a specified value."
    config_model = FillNullsConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before filling nulls.

        Returns:
            A [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard]
            ensuring the input is a Polars `LazyFrame`, and a
            [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard]
            ensuring every configured column exists in the frame schema.
        """
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(self.config.columns),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """
        Replace null values in the configured columns with the configured value.

        Args:
            data:
                Frame context whose `df` has nulls replaced.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the frame with nulls filled.
        """
        expressions = [
            pl.col(column).fill_null(self.config.value)
            for column in self.config.columns
        ]

        result = data.df.with_columns(expressions)
        return FrameContext(df=result)
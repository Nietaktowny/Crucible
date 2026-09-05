from typing import Any

import polars as pl
from pydantic import BaseModel, model_validator, Field

from crucible.errors.guards import LazyFrameInstanceGuard
from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard
from crucible.schema import build_schema

class ReplaceValuesConfig(BaseModel):
    """
    Configuration for [`ReplaceValuesStep`][crucible.steps.replace_values.ReplaceValuesStep].

    Supports exactly one of two mutually exclusive replacement modes: a
    single `old`/`new` pair, or a `mapping` of multiple old-to-new values.
    Providing both, or neither, is rejected by `validate_configuration`.
    """

    column: ColumnName = Field(
        description="Column to replace values in",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )

    old: Any | None = None
    new: Any | None = None

    mapping: dict[Any, Any] | None = None

    @model_validator(mode="after")
    def validate_configuration(self):
        has_pair = self.old is not None
        has_mapping = self.mapping is not None

        if has_pair and has_mapping:
            raise ValueError(
                "Use either old/new replacement or mapping replacement, not both."
            )

        if not has_pair and not has_mapping:
            raise ValueError(
                "Either old/new or mapping must be provided."
            )

        return self

class ReplaceValuesStep(Step):
    """
    Step that replaces values within a single column.

    Uses Polars' `replace` expression, either with a `mapping` of multiple
    old-to-new values or with a single `old`/`new` pair, and writes the
    result back into the same column name.
    """

    key = "replace_values"
    name = "Replace Values"
    description = "Replace values in a column."
    config_model = ReplaceValuesConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before replacing values.

        Returns:
            A [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard]
            ensuring the input is a Polars `LazyFrame`, and a
            [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard]
            ensuring the configured column exists in the frame schema.
        """
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard([self.config.column]),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """
        Replace values in the configured column.

        Uses `mapping` when configured, otherwise falls back to the single
        `old`/`new` pair.

        Args:
            data:
                Frame context whose `df` has values replaced.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the frame with values replaced.
        """

        if self.config.mapping:
            expression = (
                pl.col(self.config.column)
                .replace(self.config.mapping)
            )
        else:
            expression = (
                pl.col(self.config.column)
                .replace(
                    self.config.old,
                    self.config.new,
                )
            )

        result = data.df.with_columns(
            expression.alias(self.config.column)
        )
        return FrameContext(df=result)
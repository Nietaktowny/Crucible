from typing import Any

import polars as pl
from pydantic import BaseModel, model_validator, Field

from crucible.errors.guards import LazyFrameInstanceGuard
from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard
from crucible.schema import build_schema

class ReplaceValuesConfig(BaseModel):
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
    key = "replace_values"
    name = "Replace Values"
    description = "Replace values in a column."
    config_model = ReplaceValuesConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard([self.config.column]),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:

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
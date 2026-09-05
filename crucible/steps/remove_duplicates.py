from typing import Literal

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

import polars as pl
from pydantic import BaseModel, Field


class RemoveDuplicatesConfig(BaseModel):
    """
    Configuration for [`RemoveDuplicatesStep`][crucible.steps.remove_duplicates.RemoveDuplicatesStep].

    When `columns` is omitted, duplicates are detected across every column of
    the frame instead of a subset.
    """

    columns: list[ColumnName] | None = Field(
        default=None,
        description='Columns to remove duplicates in. If not specified, then duplicates will be removed in whole dataset',
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )
    keep: Literal['first', 'last'] = Field(
        default="first",
        description="Whether to keep last or first occurrence of value",
        json_schema_extra=build_schema(
            type_='literal-value',
            source='enum',
            editor='select'
        )
    )

class RemoveDuplicatesStep(Step):
    """
    Step that removes duplicate rows from the frame.

    Uses `LazyFrame.unique` with an optional `subset` of columns to determine
    duplicates and `keep` to decide whether the first or last occurrence of
    each duplicate group survives.
    """

    key = "remove_duplicates"
    name = "Remove Duplicates"
    description = "Remove duplicate rows."
    config_model = RemoveDuplicatesConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before removing duplicates.

        Returns:
            A [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard]
            always, plus a [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard]
            for the configured `columns` when a subset is specified.
        """
        if self.config.columns:
            return [
                LazyFrameInstanceGuard(),
                MissingColumnsGuard(self.config.columns),
            ]
        return [LazyFrameInstanceGuard()]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """
        Drop duplicate rows from the frame.

        Args:
            data:
                Frame context whose `df` is deduplicated.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the deduplicated lazy frame.
        """
        result = data.df.unique(
            subset=self.config.columns,
            keep=self.config.keep,
        )
        return FrameContext(df=result)
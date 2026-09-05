from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema
class SortColumnConfig(BaseModel):
    """Single sort key: a column name paired with a sort direction."""

    name: ColumnName = Field(
        description="Column to use for sorting",
        json_schema_extra=build_schema(
            type_='column-name',
            role='sort-column',
            source='input-schema',
            editor='column-select'
        )
    )
    direction: Literal['asc', 'desc'] = Field(
        default='asc',
        description='Sorting direction',
        json_schema_extra=build_schema(
            type_='literal-value',
            source='enum',
            editor='select'
        )
    )

class SortRowsConfig(BaseModel):
    """Configuration for [`SortRowsStep`][crucible.steps.sort_rows.SortRowsStep].

    Holds an ordered list of sort keys; the frame is sorted by these columns
    in the order given, each with its own ascending/descending direction.
    """

    columns: list[SortColumnConfig]

class SortRowsStep(Step):
    """
    Step that sorts rows by one or more columns.

    Each configured `SortColumnConfig` entry contributes a column name and
    direction; the resulting `by`/`descending`
    lists are passed to `LazyFrame.sort` so multiple columns act as a
    composite sort key applied left to right.
    """

    key = "sort_rows"
    name = "Sort Rows"
    description = "Sort rows based on specified columns and sort directions."
    config_model = SortRowsConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before sorting.

        Returns:
            A [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard]
            ensuring the input is a Polars `LazyFrame`, and a
            [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard]
            ensuring every configured sort column exists in the frame schema.
        """
        sort_columns = [column.name for column in self.config.columns]
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(sort_columns),
        ]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        """
        Sort the frame by the configured columns and directions.

        Args:
            data:
                Frame context whose `df` is sorted.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the sorted lazy frame.
        """
        by = [column.name for column in self.config.columns]

        descending = [
            column.direction.lower() == "desc"
            for column in self.config.columns
        ]

        result = data.df.sort(
            by=by,
            descending=descending,
        )
        return FrameContext(df=result)
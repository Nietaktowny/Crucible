import polars as pl
from pydantic import BaseModel, Field
from sqlalchemy import desc

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class SplitColumnConfig(BaseModel):
    """
    Configuration for [`SplitColumnStep`][crucible.steps.split_column.SplitColumnStep].

    `into` fixes the number of output columns produced: the source string is
    split into exactly `len(into)` parts (or `max_splits + 1` when
    `max_splits` is set), with missing trailing parts filled with null.
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
    delimiter: str = Field(
        description="Delimiter to use for splitting",
        json_schema_extra=build_schema(
            editor='text'
        )
    )

    into: list[ColumnName]

    max_splits: int | None = Field(
        default=None,
        description="Number of max splits to do",
        json_schema_extra=build_schema(
            editor='number'
        )
    )
    drop_original: bool = Field(
        default=False,
        description="Whether to drop the original column used for splitting",
        json_schema_extra=build_schema(
            editor='checkbox'
        )
    )


class SplitColumnStep(Step):
    """
    Step that splits a string column into multiple columns by a delimiter.

    Uses Polars' `str.split_exact` to split into exactly `len(into)` (or
    `max_splits + 1`) parts through a temporary struct column, then unpacks
    each part into its own named column and optionally drops the original
    source column.
    """

    key = "split_column"
    name = "Split Column"
    description = "Split a text column into multiple columns."
    config_model = SplitColumnConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before splitting the column.

        Returns:
            A [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard]
            ensuring the input is a Polars `LazyFrame`, a
            [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard]
            ensuring the configured column exists, and a
            [`ColumnsTypeGuard`][crucible.errors.ColumnsTypeGuard] ensuring
            the configured column is a string column.
        """
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard([self.config.column]),
            ColumnsTypeGuard({self.config.column: ["String"]}),
        ]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """
        Split the configured column into the configured output columns.

        Args:
            data:
                Frame context whose `df` is split.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the frame with the new columns added
            and, if `drop_original` is set, the source column removed.
        """

        split_expr = pl.col(self.config.column).str.split_exact(
            by=self.config.delimiter,
            n=len(self.config.into) - 1
            if self.config.max_splits is None
            else self.config.max_splits
        )

        result = data.df.with_columns(
            split_expr.alias("__split")
        )

        result = result.with_columns([
            pl.col("__split").struct.field(f"field_{index}").alias(column_name)
            for index, column_name in enumerate(self.config.into)
        ])

        columns_to_keep = ["__split"]

        if self.config.drop_original:
            columns_to_keep.append(self.config.column)

        result = result.drop(columns_to_keep)
        return FrameContext(df=result)
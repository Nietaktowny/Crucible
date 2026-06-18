import polars as pl
from pydantic import BaseModel, Field
from sqlalchemy import desc

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, ColumnsTypeGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class SplitColumnConfig(BaseModel):
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
    key = "split_column"
    name = "Split Column"
    description = "Split a text column into multiple columns."
    config_model = SplitColumnConfig

    def guards(self) -> list[StepGuardProtocol]:
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
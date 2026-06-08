import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext


class SplitColumnConfig(BaseModel):
    column: str
    delimiter: str

    into: list[str]

    max_splits: int | None = None
    drop_original: bool = False


class SplitColumnStep(Step):
    key = "split_column"
    name = "Split Column"
    description = "Split a text column into multiple columns."
    config_model = SplitColumnConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:

        split_expr = pl.col(self.config.column).str.split_exact(
            by=self.config.delimiter,
            n=len(self.config.into) - 1
            if self.config.max_splits is None
            else self.config.max_splits
        )

        result = data.with_columns(
            split_expr.alias("__split")
        )

        result = result.with_columns([
            pl.col("__split").struct.field(f"field_{index}").alias(column_name)
            for index, column_name in enumerate(self.config.into)
        ])

        columns_to_keep = ["__split"]

        if self.config.drop_original:
            columns_to_keep.append(self.config.column)

        return result.drop(columns_to_keep)
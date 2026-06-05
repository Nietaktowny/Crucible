import polars as pl

from crucible.models import Step


class ReorderColumnsStep(Step):
    key = "reorder_columns"

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        return data.select(self.config.columns)
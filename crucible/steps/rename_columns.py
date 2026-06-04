import polars as pl

from crucible.models import Step


class RenameColumnsStep(Step):
    key = "rename_columns"

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        return data.rename(self.config.mapping)
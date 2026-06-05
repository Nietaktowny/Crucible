import polars as pl

from crucible.models import Step

class PivotStep(Step):
    key = "pivot"

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        return data.collect().pivot(
            on=self.config.on,
            index=self.config.index,
            values=self.config.values,
            aggregate_function=self.config.aggregate_function,
        ).lazy()
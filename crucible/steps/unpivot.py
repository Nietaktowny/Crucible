import polars as pl

from crucible.models import Step

class UnpivotStep(Step):
    key = "unpivot"

    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        return data.unpivot(
            on=self.config.on,
            index=self.config.index,
            variable_name=self.config.variable_name,
            value_name=self.config.value_name,
        )
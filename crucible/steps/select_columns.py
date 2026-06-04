from crucible.models import Step
import polars as pl

class SelectColumnsStep(Step):
    key = "select_columns"
    
    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        return data.select(self.config.columns)
from crucible.models import Step
import polars as pl
from pydantic import BaseModel

from crucible.models import StepConfig

class SelectColumnsConfig(BaseModel):
    columns: list[str]

class SelectColumnsStep(Step):
    key = "select_columns"
    name = "Select Columns"
    description = "Select a subset of columns from the data."
    config_model = SelectColumnsConfig
    
    def execute(self, data: pl.LazyFrame) -> pl.LazyFrame:
        return data.select(self.config.columns)
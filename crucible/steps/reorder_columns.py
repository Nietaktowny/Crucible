import polars as pl
from pydantic import BaseModel


from crucible.models import Step, StepExecutionContext

class ReorderColumnsConfig(BaseModel):
    columns: list[str]
class ReorderColumnsStep(Step):
    key = "reorder_columns"
    name = "Reorder Columns"
    description = "Reorder columns based on a specified list of column names."
    config_model = ReorderColumnsConfig

    def execute(self, data: pl.LazyFrame, context: StepExecutionContext = None) -> pl.LazyFrame:
        return data.select(self.config.columns)
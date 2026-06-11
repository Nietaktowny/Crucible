from crucible.models import Step, FrameContext
import polars as pl
from pydantic import BaseModel

from crucible.models import StepExecutionContext

class SelectColumnsConfig(BaseModel):
    columns: list[str]

class SelectColumnsStep(Step):
    key = "select_columns"
    name = "Select Columns"
    description = "Select a subset of columns from the data."
    config_model = SelectColumnsConfig
    
    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        result = data.df.select(self.config.columns)
        return FrameContext(df=result, schema=data.schema)
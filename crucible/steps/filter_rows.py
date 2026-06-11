import polars as pl
from pydantic import BaseModel

from crucible.declarative import Condition, ConditionBuilder
from crucible.models import Step, StepExecutionContext, FrameContext

class FilterRowsConfig(BaseModel):
    condition: Condition

class FilterRowsStep(Step):
    key = "filter_rows"
    name = "Filter Rows"
    description = "Filter rows based on a declarative condition."
    config_model = FilterRowsConfig

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        predicate = ConditionBuilder().build(self.config.condition)

        result = data.df.filter(predicate)
        return FrameContext(df=result, schema=data.schema)
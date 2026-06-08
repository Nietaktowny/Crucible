import polars as pl
from pydantic import BaseModel

from crucible.declarative import Condition, ConditionBuilder
from crucible.models import Step, StepExecutionContext

class FilterRowsConfig(BaseModel):
    condition: Condition

class FilterRowsStep(Step):
    key = "filter_rows"
    name = "Filter Rows"
    description = "Filter rows based on a declarative condition."
    config_model = FilterRowsConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        predicate = ConditionBuilder().build(self.config.condition)

        return data.filter(predicate)
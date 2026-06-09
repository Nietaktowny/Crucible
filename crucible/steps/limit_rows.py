from typing import Literal

from crucible.models import Step
import polars as pl
from pydantic import BaseModel

from crucible.models import StepExecutionContext

class LimitRowsConfig(BaseModel):
    limit: int
    mode: Literal['head', 'tail']

class LimitRowsStep(Step):
    key = "limit_rows"
    name = "Limit rows"
    description = "Limit rows to first or last n rows"
    config_model = LimitRowsConfig
    
    def execute(self, data: pl.LazyFrame, context: StepExecutionContext = None) -> pl.LazyFrame:
        if self.config.mode == 'head':
            return data.head(self.config.limit)
        elif self.config.mode == 'tail':
            return data.tail(self.config.limit)
        else:
            raise ValueError(f"Unknown limit rows mode for LimitRowsStep, passed: {self.config.mode}. Expected one of: {['head', 'tail']}")
            
from typing import Literal

from crucible.models import Step, FrameContext, StepGuardProtocol
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
    
    def guards(self) -> list[StepGuardProtocol]:
        return []
    
    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        if self.config.mode == 'head':
            result = data.df.head(self.config.limit)
        elif self.config.mode == 'tail':
            result = data.df.tail(self.config.limit)
        else:
            raise ValueError(f"Unknown limit rows mode for LimitRowsStep, passed: {self.config.mode}. Expected one of: {['head', 'tail']}")
        return FrameContext(df=result, schema=data.schema)
            
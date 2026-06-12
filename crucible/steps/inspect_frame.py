import polars as pl
from pydantic import BaseModel

from crucible.models import Step, FrameContext, StepGuardProtocol, StepExecutionContext
from crucible.errors import LazyFrameInstanceGuard

class InspectFrameConfig(BaseModel):
    preview_limit: int = 500

class InspectFrameStep(Step):
    key = "__inspect_frame"
    name = "Inspect Frame Details"
    description = "Execute steps till now, and calculate preview and statistics for frame."
    config_model = InspectFrameConfig
    
    def guards(self) -> list[StepGuardProtocol]:
        return [LazyFrameInstanceGuard()]
    
    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:        
        preview = data.df.limit(self.config.preview_limit).collect()
        row_count = data.df.select(pl.len()).collect().item()
        
        return FrameContext(
            df=data.df,
            preview=preview,
            row_count=row_count
        )
import polars as pl
from pydantic import BaseModel


from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard

class ReorderColumnsConfig(BaseModel):
    columns: list[str]
class ReorderColumnsStep(Step):
    key = "reorder_columns"
    name = "Reorder Columns"
    description = "Reorder columns based on a specified list of column names."
    config_model = ReorderColumnsConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(self.config.columns),
        ]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        result = data.df.select(self.config.columns)
        return FrameContext(df=result)
import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard

class RenameColumnsConfig(BaseModel):
    mapping: dict[str, str]
class RenameColumnsStep(Step):
    key = "rename_columns"
    name = "Rename Columns"
    description = "Rename columns based on a provided mapping."
    config_model = RenameColumnsConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(list(self.config.mapping.keys())),
        ]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        result = data.df.rename(self.config.mapping)
        return FrameContext(df=result)
import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingColumnsGuard

class UnpivotConfig(BaseModel):
    on: list[str]
    index: list[str]
    variable_name: str
    value_name: str

class UnpivotStep(Step):
    key = "unpivot"
    name = "Unpivot"
    description = "Unpivot the data from wide to long format."
    config_model = UnpivotConfig

    def guards(self) -> list[StepGuardProtocol]:
        all_columns = self.config.on + self.config.index
        return [MissingColumnsGuard(all_columns)]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        result = data.df.unpivot(
            on=self.config.on,
            index=self.config.index,
            variable_name=self.config.variable_name,
            value_name=self.config.value_name,
        )
        return FrameContext(df=result, schema=data.schema)
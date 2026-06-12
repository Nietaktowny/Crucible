from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingColumnsGuard


class DropColumnsConfig(BaseModel):
    columns: list[str]


class DropColumnsStep(Step):
    key = "drop_columns"
    name = "Drop columns"
    description = "Drop specified columns"
    config_model = DropColumnsConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [MissingColumnsGuard(self.config.columns)]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        result = data.df.drop(self.config.columns)
        return FrameContext(df=result)
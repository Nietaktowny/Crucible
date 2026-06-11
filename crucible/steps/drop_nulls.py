import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import MissingColumnsGuard


class DropNullsConfig(BaseModel):
    columns: list[str] | None = None


class DropNullsStep(Step):
    key = "drop_nulls"
    name = "Drop Nulls"
    description = "Remove rows containing null values."
    config_model = DropNullsConfig

    def guards(self) -> list[StepGuardProtocol]:
        if self.config.columns:
            return [MissingColumnsGuard(self.config.columns)]
        return []

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        result = data.df.drop_nulls(
            subset=self.config.columns,
        )
        return FrameContext(df=result, schema=data.schema)
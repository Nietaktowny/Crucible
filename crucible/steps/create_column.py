import polars as pl
from pydantic import BaseModel

from crucible.declarative import Expression, ExpressionBuilder
from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol


class CreateColumnConfig(BaseModel):
    name: str
    expr: Expression


class CreateColumnStep(Step):
    key = "create_column"
    name = "Create Column"
    description = "Create a new column from a declarative expression."
    config_model = CreateColumnConfig

    def guards(self) -> list[StepGuardProtocol]:
        return []

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        expression = ExpressionBuilder().build(self.config.expr)

        result = data.df.with_columns(
            expression.alias(self.config.name)
        )
        return FrameContext(df=result, schema=data.schema)
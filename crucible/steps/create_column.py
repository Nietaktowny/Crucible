import polars as pl
from pydantic import BaseModel

from crucible.declarative import Expression, ExpressionBuilder
from crucible.models import Step, StepExecutionContext


class CreateColumnConfig(BaseModel):
    name: str
    expr: Expression


class CreateColumnStep(Step):
    key = "create_column"
    name = "Create Column"
    description = "Create a new column from a declarative expression."
    config_model = CreateColumnConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        expression = ExpressionBuilder().build(self.config.expr)

        return data.with_columns(
            expression.alias(self.config.name)
        )
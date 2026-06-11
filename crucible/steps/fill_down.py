import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext


class FillDownConfig(BaseModel):
    columns: list[str]


class FillDownStep(Step):
    key = "fill_down"
    name = "Fill Down"
    description = "Fill null values with the previous non-null value."
    config_model = FillDownConfig

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        expressions = [
            pl.col(column).forward_fill()
            for column in self.config.columns
        ]

        result = data.df.with_columns(expressions)
        return FrameContext(df=result, schema=data.schema)
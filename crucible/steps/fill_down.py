import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class FillDownConfig(BaseModel):
    columns: list[ColumnName]  = Field(
        description="List of columns to drop",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )


class FillDownStep(Step):
    key = "fill_down"
    name = "Fill Down"
    description = "Fill null values with the previous non-null value."
    config_model = FillDownConfig

    def guards(self) -> list[StepGuardProtocol]:
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(self.config.columns),
        ]

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
        return FrameContext(df=result)
import polars as pl
from pydantic import BaseModel, Field


from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema
class ReorderColumnsConfig(BaseModel):
    columns: list[ColumnName] = Field(
        description="Columns order",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )
    
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
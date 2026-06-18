from crucible.models import Step, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema
from pydantic import BaseModel, Field

from crucible.models import StepExecutionContext

class SelectColumnsConfig(BaseModel):
    columns: list[ColumnName] = Field(
        description="Columns that should remain in the dataset.",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )

class SelectColumnsStep(Step):
    key = "select_columns"
    name = "Select Columns"
    description = "Select a subset of columns from the data."
    config_model = SelectColumnsConfig
    
    def guards(self) -> list[StepGuardProtocol]:
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(self.config.columns)
        ]
    
    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        result = data.df.select(self.config.columns)
        return FrameContext(df=result)
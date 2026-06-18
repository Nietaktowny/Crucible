from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class DropColumnsConfig(BaseModel):
    columns: list[ColumnName]  = Field(
        description="List of columns to drop",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )


class DropColumnsStep(Step):
    key = "drop_columns"
    name = "Drop columns"
    description = "Drop specified columns"
    config_model = DropColumnsConfig

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
        result = data.df.drop(self.config.columns)
        return FrameContext(df=result)
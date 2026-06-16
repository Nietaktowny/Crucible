import polars as pl
from pydantic import BaseModel

from crucible.errors.guards import LazyFrameInstanceGuard
from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard


class DropNullsConfig(BaseModel):
    columns: list[ColumnName] | None = None


class DropNullsStep(Step):
    key = "drop_nulls"
    name = "Drop Nulls"
    description = "Remove rows containing null values."
    config_model = DropNullsConfig

    def guards(self) -> list[StepGuardProtocol]:
        if self.config.columns:
            return [
                LazyFrameInstanceGuard(),
                MissingColumnsGuard(self.config.columns),
        ]
        return [LazyFrameInstanceGuard()]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        result = data.df.drop_nulls(
            subset=self.config.columns,
        )
        return FrameContext(df=result)
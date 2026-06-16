
from typing import Literal

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard

import polars as pl
from pydantic import BaseModel

class PivotConfig(BaseModel):
    on: list[ColumnName]
    index: list[ColumnName]
    values: list[ColumnName]
    aggregate_function: Literal[
        'first',
        'last',
        'sum',
        'min',
        'max',
        'mean',
        'median',
        'len'
    ] = 'first'

class PivotStep(Step):
    key = "pivot"
    name = "Pivot"
    description = "Pivot the data from long to wide format."
    config_model = PivotConfig

    def guards(self) -> list[StepGuardProtocol]:
        all_columns = self.config.on + self.config.index + self.config.values
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(all_columns),
        ]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        result = data.df.collect().pivot(
            on=self.config.on,
            index=self.config.index,
            values=self.config.values,
            aggregate_function=self.config.aggregate_function,
        ).lazy()
        return FrameContext(df=result)
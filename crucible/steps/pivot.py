
from typing import Literal

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

import polars as pl
from pydantic import BaseModel, Field

class PivotConfig(BaseModel):
    on: list[ColumnName] = Field(
        description="Columns to pivot on",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            editor='column-multiselect',
            source='input-schema'
        )
    )
    index: list[ColumnName] = Field(
        description="Columns that will be used as an index. They will stay unchanged.",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )
    values: list[ColumnName] = Field(
        description="Columns that will be used as values for pivoted columns.",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-multiselect'
        )
    )
    aggregate_function: Literal[
        'first',
        'last',
        'sum',
        'min',
        'max',
        'mean',
        'median',
        'len'
    ] = Field(
        default='first',
        description="How values would be aggregated after pivot.",
        json_schema_extra=build_schema(
            type_='literal-value',
            source='enum',
            editor='select'
        )
    )

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
from typing import Literal

import polars as pl
from pydantic import BaseModel, Field

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard
from crucible.schema import build_schema

class AggregationConfig(BaseModel):
    column: ColumnName = Field(
        description="Column to use for aggregation",
        json_schema_extra=build_schema(
            type_='column-name',
            role='input-column',
            source='input-schema',
            editor='column-select'
        )
    )
    function: Literal[
        "sum",
        "min",
        "max",
        "mean",
        "median",
        "count",
        "len",
        "first",
        "last",
        "n_unique",
    ] = Field(
        description="Aggregation function to use.",
        json_schema_extra=build_schema(
            type_='literal-value',
            editor='select',
            source='enum'
        )
    )
    alias: ColumnName | None = Field(
        default=None,
        description="Alias column name to use",
        json_schema_extra=build_schema(
            type_='column-name',
            role='output-column',
            editor='text'
        )
    )


class GroupByConfig(BaseModel):
    by: list[str]
    aggregations: list[AggregationConfig]


class GroupByStep(Step):
    key = "group_by"
    name = "Group By"
    description = "Group rows and calculate aggregations."
    config_model = GroupByConfig

    def guards(self) -> list[StepGuardProtocol]:
        columns_to_check = self.config.by.copy()
        for agg in self.config.aggregations:
            if agg.function != "len":  # 'len' doesn't require a column
                columns_to_check.append(agg.column)
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(columns_to_check),
        ]

    def _build_aggregation(self, aggregation: AggregationConfig) -> pl.Expr:
        column = pl.col(aggregation.column)

        match aggregation.function:
            case "sum":
                expr = column.sum()
            case "min":
                expr = column.min()
            case "max":
                expr = column.max()
            case "mean":
                expr = column.mean()
            case "median":
                expr = column.median()
            case "count":
                expr = column.count()
            case "len":
                expr = pl.len()
            case "first":
                expr = column.first()
            case "last":
                expr = column.last()
            case "n_unique":
                expr = column.n_unique()
            case _:
                raise ValueError(f"Unsupported aggregation: {aggregation.function}")

        if aggregation.alias:
            expr = expr.alias(aggregation.alias)

        return expr

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        expressions = [
            self._build_aggregation(aggregation)
            for aggregation in self.config.aggregations
        ]

        result = data.df.group_by(self.config.by).agg(expressions)
        return FrameContext(df=result)
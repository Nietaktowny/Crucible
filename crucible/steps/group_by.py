from typing import Literal

import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext


class AggregationConfig(BaseModel):
    column: str
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
    ]
    alias: str | None = None


class GroupByConfig(BaseModel):
    by: list[str]
    aggregations: list[AggregationConfig]


class GroupByStep(Step):
    key = "group_by"
    name = "Group By"
    description = "Group rows and calculate aggregations."
    config_model = GroupByConfig

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
        return FrameContext(df=result, schema=data.schema)
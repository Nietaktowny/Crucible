from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field


ExpressionOperation = Literal[
    "add",
    "subtract",
    "multiply",
    "divide",
    "safe_divide",
    "round",
    "abs",
    "concat",
    "coalesce",
    "upper",
    "lower",
    "trim",
]


class ColumnExpression(BaseModel):
    column: str


class ValueExpression(BaseModel):
    value: Any


class OperationExpression(BaseModel):
    op: ExpressionOperation
    args: list[Expression] = Field(default_factory=list)


Expression = Annotated[
    Union[
        ColumnExpression,
        ValueExpression,
        OperationExpression,
    ],
    Field(union_mode="left_to_right"),
]
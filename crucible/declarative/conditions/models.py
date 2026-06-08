from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from crucible.declarative.expressions import Expression


ComparisonOperator = Literal[
    "=",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "contains",
    "starts_with",
    "ends_with",
    "is_null",
    "is_not_null",
    "is_in",
]


class ComparisonCondition(BaseModel):
    left: Expression
    operator: ComparisonOperator
    right: Expression | None = None


class AndCondition(BaseModel):
    logic: Literal["and"]
    conditions: list[Condition]


class OrCondition(BaseModel):
    logic: Literal["or"]
    conditions: list[Condition]


class NotCondition(BaseModel):
    logic: Literal["not"]
    condition: Condition


Condition = Annotated[
    Union[
        ComparisonCondition,
        AndCondition,
        OrCondition,
        NotCondition,
    ],
    Field(union_mode="left_to_right"),
]
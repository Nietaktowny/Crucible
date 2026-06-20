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
"""
Supported operators for comparison conditions.

The operators are intentionally simple and workflow-friendly. They map later
to Polars expressions through
[`ConditionBuilder`][crucible.declarative.conditions.builder.ConditionBuilder].
"""


class ComparisonCondition(BaseModel):
    """
    Declarative condition that compares a left expression with an optional right
    expression.

    This model represents the most basic condition type used by filtering
    workflows. The left side is always required. The right side is required
    only for binary operators such as `=`, `!=`, `>`, `contains`, or `is_in`.

    Unary operators such as `is_null` and `is_not_null` do not require a right
    expression.

    Example:
        ```yaml
        left:
          column: country
        operator: "="
        right:
          value: PL
        ```
    """

    left: Expression
    """Left-side expression used by the comparison."""

    operator: ComparisonOperator
    """Comparison operator to apply."""

    right: Expression | None = None
    """Optional right-side expression used by binary comparison operators."""


class AndCondition(BaseModel):
    """
    Declarative logical AND condition.

    All child conditions must evaluate to true for the resulting condition to
    match a row.

    Example:
        ```yaml
        logic: and
        conditions:
          - left:
              column: country
            operator: "="
            right:
              value: PL
          - left:
              column: status
            operator: "!="
            right:
              value: cancelled
        ```
    """

    logic: Literal["and"]
    """Logical discriminator identifying this condition as an AND condition."""

    conditions: list[Condition]
    """Child conditions combined with logical AND."""


class OrCondition(BaseModel):
    """
    Declarative logical OR condition.

    At least one child condition must evaluate to true for the resulting
    condition to match a row.
    """

    logic: Literal["or"]
    """Logical discriminator identifying this condition as an OR condition."""

    conditions: list[Condition]
    """Child conditions combined with logical OR."""


class NotCondition(BaseModel):
    """
    Declarative logical NOT condition.

    Negates a single child condition.
    """

    logic: Literal["not"]
    """Logical discriminator identifying this condition as a NOT condition."""

    condition: Condition
    """Child condition to negate."""


Condition = Annotated[
    Union[
        ComparisonCondition,
        AndCondition,
        OrCondition,
        NotCondition,
    ],
    Field(union_mode="left_to_right"),
]
"""
Union type representing any supported declarative condition.

The union uses `left_to_right` mode because
[`ComparisonCondition`][crucible.declarative.conditions.models.ComparisonCondition]
does not use a `logic` discriminator, while logical conditions do.

This type is consumed by
[`ConditionBuilder`][crucible.declarative.conditions.builder.ConditionBuilder]
to produce executable Polars expressions.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field

from crucible.models import ColumnName


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
"""
Supported operation names for declarative expressions.

Operations are translated into Polars expressions by
[`ExpressionBuilder`][crucible.declarative.expressions.builder.ExpressionBuilder].
"""


class ColumnExpression(BaseModel):
    """
    Declarative expression that references an input column.

    This expression is equivalent to selecting a column in Polars with
    `pl.col(...)`.

    Example:
        ```yaml
        column: net_price
        ```
    """

    column: ColumnName
    """Name of the input column referenced by the expression."""


class ValueExpression(BaseModel):
    """
    Declarative expression that represents a literal value.

    Literal values are converted to Polars literals with `pl.lit(...)`.

    Example:
        ```yaml
        value: 100
        ```
    """

    value: Any
    """Literal value used by the expression."""


class OperationExpression(BaseModel):
    """
    Declarative expression that applies an operation to child expressions.

    Operations are used to build calculated values from columns, literals,
    or other nested operations.

    Example:
        ```yaml
        op: add
        args:
          - column: net_price
          - column: tax
        ```
    """

    op: ExpressionOperation
    """Operation name to apply."""

    args: list[Expression] = Field(default_factory=list)
    """Child expressions used as operation arguments."""


Expression = Annotated[
    Union[
        ColumnExpression,
        ValueExpression,
        OperationExpression,
    ],
    Field(union_mode="left_to_right"),
]
"""
Union type representing any supported declarative expression.

The union uses `left_to_right` mode because the expression variants do not
currently use an explicit discriminator field.

This type is consumed by
[`ExpressionBuilder`][crucible.declarative.expressions.builder.ExpressionBuilder]
to produce executable Polars expressions.
"""
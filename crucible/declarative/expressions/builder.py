from __future__ import annotations

import polars as pl

from crucible.declarative.expressions.models import (
    ColumnExpression,
    Expression,
    OperationExpression,
    ValueExpression,
)


class ExpressionBuilder:
    """
    Builds Polars expressions from declarative expression definitions.

    The builder converts expression models such as
    [`ColumnExpression`][crucible.declarative.expressions.models.ColumnExpression],
    [`ValueExpression`][crucible.declarative.expressions.models.ValueExpression],
    and
    [`OperationExpression`][crucible.declarative.expressions.models.OperationExpression]
    into executable `polars.Expr` objects.

    This component is used by workflow steps that need computed values, for
    example filtering rows, creating calculated columns, or building
    declarative conditions.

    Example:
        ```python
        expression = OperationExpression(
            op="add",
            args=[
                ColumnExpression(column="net_price"),
                ColumnExpression(column="tax"),
            ],
        )

        expr = ExpressionBuilder().build(expression)
        ```
    """

    def build(self, expression: Expression) -> pl.Expr:
        """
        Convert a declarative expression into a Polars expression.

        Supported expression types:

        - column references
        - literal values
        - operation expressions

        Args:
            expression:
                Declarative expression definition.

        Returns:
            Equivalent Polars expression.

        Raises:
            TypeError:
                If the expression type is not supported.
        """
        if isinstance(expression, ColumnExpression):
            return pl.col(expression.column)

        if isinstance(expression, ValueExpression):
            return pl.lit(expression.value)

        if isinstance(expression, OperationExpression):
            return self._build_operation(expression)

        raise TypeError(
            f"Unsupported expression type: {type(expression).__name__}"
        )

    def _build_operation(self, expression: OperationExpression) -> pl.Expr:
        """
        Build a Polars expression for a declarative operation.

        Supported operations:

        - `add`
        - `subtract`
        - `multiply`
        - `divide`
        - `safe_divide`
        - `round`
        - `abs`
        - `concat`
        - `coalesce`
        - `upper`
        - `lower`
        - `trim`

        Args:
            expression:
                Declarative operation expression.

        Returns:
            Equivalent Polars expression.

        Raises:
            ValueError:
                If the operation name is unsupported or the argument count is
                invalid.
        """
        args = [self.build(arg) for arg in expression.args]

        match expression.op:
            case "add":
                self._require_args(expression, 2)
                return args[0] + args[1]
            case "subtract":
                self._require_args(expression, 2)
                return args[0] - args[1]
            case "multiply":
                self._require_args(expression, 2)
                return args[0] * args[1]
            case "divide":
                self._require_args(expression, 2)
                return args[0] / args[1]
            case "safe_divide":
                self._require_args(expression, 2)
                return (
                    pl.when(args[1].is_null() | (args[1] == 0))
                    .then(None)
                    .otherwise(args[0] / args[1])
                )
            case "round":
                self._require_args(expression, 2)
                decimals_arg = expression.args[1]

                if not isinstance(decimals_arg, ValueExpression):
                    raise ValueError(
                        "Operation 'round' requires second argument to be a "
                        "literal integer."
                    )

                if not isinstance(decimals_arg.value, int):
                    raise ValueError(
                        "Operation 'round' requires second argument to be a "
                        "literal integer."
                    )

                return args[0].round(decimals_arg.value)
            case "abs":
                self._require_args(expression, 1)
                return args[0].abs()
            case "concat":
                self._require_min_args(expression, 1)
                return pl.concat_str(args, separator="")
            case "coalesce":
                self._require_min_args(expression, 1)
                return pl.coalesce(args)
            case "upper":
                self._require_args(expression, 1)
                return args[0].str.to_uppercase()
            case "lower":
                self._require_args(expression, 1)
                return args[0].str.to_lowercase()
            case "trim":
                self._require_args(expression, 1)
                return args[0].str.strip_chars()
            case _:
                raise ValueError(
                    f"Unsupported expression operation: {expression.op}"
                )

    def _require_args(
        self,
        expression: OperationExpression,
        count: int,
    ) -> None:
        """
        Validate that an operation has exactly the expected number of arguments.

        Args:
            expression:
                Operation expression to validate.

            count:
                Required number of arguments.

        Raises:
            ValueError:
                If the operation has a different number of arguments.
        """
        actual = len(expression.args)

        if actual != count:
            raise ValueError(
                f"Operation '{expression.op}' requires {count} arguments, "
                f"got {actual}."
            )

    def _require_min_args(
        self,
        expression: OperationExpression,
        minimum: int,
    ) -> None:
        """
        Validate that an operation has at least the required number of arguments.

        Args:
            expression:
                Operation expression to validate.

            minimum:
                Minimum accepted number of arguments.

        Raises:
            ValueError:
                If the operation has too few arguments.
        """
        actual = len(expression.args)

        if actual < minimum:
            raise ValueError(
                f"Operation '{expression.op}' requires at least {minimum} "
                f"argument(s), got {actual}."
            )
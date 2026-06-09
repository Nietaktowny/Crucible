from __future__ import annotations

import polars as pl

from crucible.declarative.expressions.models import (
    ColumnExpression,
    Expression,
    OperationExpression,
    ValueExpression,
)


class ExpressionBuilder:
    def build(self, expression: Expression) -> pl.Expr:
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
                    raise ValueError("Operation 'round' requires second argument to be a literal integer.")

                if not isinstance(decimals_arg.value, int):
                    raise ValueError("Operation 'round' requires second argument to be a literal integer.")

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
        actual = len(expression.args)

        if actual < minimum:
            raise ValueError(
                f"Operation '{expression.op}' requires at least {minimum} "
                f"argument(s), got {actual}."
            )
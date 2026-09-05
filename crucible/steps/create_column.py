import polars as pl
from pydantic import BaseModel, Field

from crucible.declarative import Expression, ExpressionBuilder
from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import LazyFrameInstanceGuard
from crucible.schema import build_schema

class CreateColumnConfig(BaseModel):
    """
    Configuration for [`CreateColumnStep`][crucible.steps.create_column.CreateColumnStep].

    If `name` matches an existing column, that column is overwritten with the
    expression result instead of a new one being added.
    """

    name: ColumnName
    expr: Expression = Field(
        description="Expression used to create new column",
        json_schema_extra=build_schema(
            type_='expression',
            role='output-column'
        )
    )

class CreateColumnStep(Step):
    """
    Step that adds a computed column built from a declarative expression.

    The configured [`Expression`][crucible.declarative.expressions.Expression]
    is translated into a Polars expression via
    [`ExpressionBuilder`][crucible.declarative.expressions.ExpressionBuilder]
    and applied with `LazyFrame.with_columns`, aliased to the configured
    column name.
    """

    key = "create_column"
    name = "Create Column"
    description = "Create a new column from a declarative expression."
    config_model = CreateColumnConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before creating the column.

        Returns:
            A single [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard]
            ensuring the input frame is a Polars `LazyFrame`.
        """
        return [LazyFrameInstanceGuard()]

    def execute(
        self,
        data: FrameContext,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        """
        Compute the configured expression and add it as a new column.

        Args:
            data:
                Frame context whose `df` receives the new column.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the frame with the added column.
        """
        expression = ExpressionBuilder().build(self.config.expr)

        result = data.df.with_columns(
            expression.alias(self.config.name)
        )
        return FrameContext(df=result)
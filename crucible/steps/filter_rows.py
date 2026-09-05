import polars as pl
from pydantic import BaseModel

from crucible.declarative import Condition, ConditionBuilder
from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol
from crucible.errors import LazyFrameInstanceGuard

class FilterRowsConfig(BaseModel):
    """
    Configuration for [`FilterRowsStep`][crucible.steps.filter_rows.FilterRowsStep].

    Holds the declarative condition used to keep or drop rows.
    """

    condition: Condition

class FilterRowsStep(Step):
    """
    Step that keeps only rows matching a declarative condition.

    The configured [`Condition`][crucible.declarative.conditions.models.Condition]
    is translated into a Polars predicate via
    [`ConditionBuilder`][crucible.declarative.conditions.builder.ConditionBuilder]
    and applied with `LazyFrame.filter`, so rows for which the predicate is
    false or null are removed.
    """

    key = "filter_rows"
    name = "Filter Rows"
    description = "Filter rows based on a declarative condition."
    config_model = FilterRowsConfig

    def guards(self) -> list[StepGuardProtocol]:
        """
        Return guards required before filtering.

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
        Filter rows using the configured declarative condition.

        Args:
            data:
                Frame context whose `df` is filtered.

            context:
                Unused execution context. Present for interface compatibility.

        Returns:
            New frame context wrapping the filtered lazy frame.
        """
        predicate = ConditionBuilder().build(self.config.condition)

        result = data.df.filter(predicate)
        return FrameContext(df=result)
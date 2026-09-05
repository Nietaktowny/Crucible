import polars as pl
from pydantic import BaseModel

from crucible.models import Step, StepExecutionContext, FrameContext, StepGuardProtocol, ColumnName
from crucible.errors import MissingColumnsGuard, LazyFrameInstanceGuard

class UnpivotConfig(BaseModel):
    """Configuration for unpivoting data from wide to long format."""

    on: list[ColumnName]
    index: list[ColumnName]
    variable_name: ColumnName
    value_name: ColumnName

class UnpivotStep(Step):
    """Melt the `on` columns into two long-format columns using `LazyFrame.unpivot`.

    The `index` columns are kept as-is and repeated for each melted value; the
    former column names are stored in `variable_name` and their values in
    `value_name`.
    """

    key = "unpivot"
    name = "Unpivot"
    description = "Unpivot the data from wide to long format."
    config_model = UnpivotConfig

    def guards(self) -> list[StepGuardProtocol]:
        """Guard against a non-lazy frame or missing `on`/`index` columns.

        Returns:
            List containing a [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard]
            and a [`MissingColumnsGuard`][crucible.errors.MissingColumnsGuard] covering all
            columns referenced by `on` and `index`.
        """
        all_columns = self.config.on + self.config.index
        return [
            LazyFrameInstanceGuard(),
            MissingColumnsGuard(all_columns),
        ]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        """Unpivot the frame from wide to long format.

        Args:
            data:
                Current frame context whose `df` must contain the columns
                referenced by `on` and `index`.

            context:
                Unused execution context.

        Returns:
            Updated frame context with the unpivoted lazy frame.
        """
        result = data.df.unpivot(
            on=self.config.on,
            index=self.config.index,
            variable_name=self.config.variable_name,
            value_name=self.config.value_name,
        )
        return FrameContext(df=result)
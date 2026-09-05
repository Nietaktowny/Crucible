import polars as pl
from pydantic import BaseModel

from crucible.models import Step, FrameContext, StepGuardProtocol, StepExecutionContext
from crucible.errors import LazyFrameInstanceGuard

class InspectFrameConfig(BaseModel):
    """Configuration for collecting a preview and row count of the current frame."""

    preview_limit: int = 500

class InspectFrameStep(Step):
    """Collect a bounded preview and total row count of the frame as it stands at this point in the pipeline.

    This is a system step: its key `"__inspect_frame"` starts with `__`, so
    the executor counts it toward `WorkflowRuntimeStatistics.system_steps`
    rather than the user-authored step count. It does not transform the data
    itself; it triggers eager collection (a bounded preview and a full-frame
    row count) so intermediate results can be inspected, and passes the
    original lazy frame through unchanged.
    """

    key = "__inspect_frame"
    name = "Inspect Frame Details"
    description = "Execute steps till now, and calculate preview and statistics for frame."
    config_model = InspectFrameConfig

    def guards(self) -> list[StepGuardProtocol]:
        """Guard against a non-lazy frame.

        Returns:
            List containing a single [`LazyFrameInstanceGuard`][crucible.errors.LazyFrameInstanceGuard].
        """
        return [LazyFrameInstanceGuard()]

    def execute(self, data: FrameContext, context: StepExecutionContext = None) -> FrameContext:
        """Collect a preview and row count without altering the underlying lazy frame.

        Args:
            data:
                Current frame context to inspect.

            context:
                Unused execution context.

        Returns:
            Updated frame context carrying the original `df`, plus the
            collected `preview` (limited to `preview_limit` rows) and the
            total `row_count`.
        """
        preview = data.df.limit(self.config.preview_limit).collect()
        row_count = data.df.select(pl.len()).collect().item()
        
        return FrameContext(
            df=data.df,
            preview=preview,
            row_count=row_count
        )
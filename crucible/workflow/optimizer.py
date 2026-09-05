from itertools import pairwise
import logging

from crucible.models import WorkflowExecutionPlan, WorkflowRunConfig

logger = logging.getLogger(__name__)

class WorkflowOptimizer:
    """Applies cheap, purely structural optimizations to a compiled execution plan.

    Runs after compilation and before execution, mutating the plan in place
    and recording each optimization it applies to
    `WorkflowExecutionPlan.applied_optimizations` for visibility (e.g. when
    printed via `WorkflowCompiler.print_execution_plan`).
    """

    def _apply_columns_optimization(self): ...

    def optimize(self, workflow: WorkflowExecutionPlan, *, config: WorkflowRunConfig | None = None) -> WorkflowExecutionPlan:
        """Push column selection into an immediately preceding read step.

        When a `read_*` step is directly followed by a `select_columns`
        step, and the read step hasn't already been given an explicit
        `columns` list, this copies the `select_columns` step's column list
        onto the read step's config. This lets IO managers that support
        column pruning (see `crucible.io`) skip reading unused columns
        entirely, rather than reading everything and then discarding
        columns in a later step. The `select_columns` step itself is left
        in place; the projection just becomes redundant rather than removed.

        Args:
            workflow (WorkflowExecutionPlan): Compiled execution plan to optimize, mutated in place.
            config (WorkflowRunConfig | None, optional): Unused by this optimization. Defaults to None.

        Returns:
            WorkflowExecutionPlan: The same plan instance, with optimizations applied.
        """
        for prev_node, next_node in pairwise(workflow.steps_execution_plan):
            if prev_node.step.key.startswith("read_") and next_node.step.key == "select_columns":
                if hasattr(prev_node.step.config, "columns") and prev_node.step.config.columns is None:
                    prev_node.step.config.columns = next_node.step.config.columns
                    workflow.applied_optimizations.append("Columns selection moved into read step")
        return workflow

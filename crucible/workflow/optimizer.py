from itertools import pairwise
import logging

from crucible.models import WorkflowExecutionPlan, WorkflowRunConfig

logger = logging.getLogger(__name__)

class WorkflowOptimizer:
    
    def _apply_columns_optimization(self): ...    

    def optimize(self, workflow: WorkflowExecutionPlan, *, config: WorkflowRunConfig | None = None) -> WorkflowExecutionPlan:
        for prev_node, next_node in pairwise(workflow.steps_execution_plan):
            if prev_node.step.key.startswith("read_") and next_node.step.key == "select_columns":
                if hasattr(prev_node.step.config, "columns") and prev_node.step.config.columns is None:
                    prev_node.step.config.columns = next_node.step.config.columns
                    workflow.applied_optimizations.append("Columns selection moved into read step")
        return workflow
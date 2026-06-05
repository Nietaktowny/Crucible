import logging

from crucible.models import Workflow, StepExecutionPlan, WorkflowExecutionPlan
from crucible.workflow.registry import StepsRegistry


logger = logging.getLogger(__name__)

class WorkflowCompiler:
    def __init__(self) -> None:
        self.steps_registry = StepsRegistry()

    def compile(self, workflow: Workflow) -> WorkflowExecutionPlan:
        steps_execution_plan = []
        for step_config in workflow.steps:
            step = self.steps_registry.get_step(step_config.key, step_config=step_config)
            if not step:
                raise ValueError(f"Step with key {step_config.key} not found in registry")
            
            step_execution_plan = StepExecutionPlan(
                step=step,
                config=step_config
            )
            steps_execution_plan.append(step_execution_plan)
            
        workflow_execution_plan = WorkflowExecutionPlan(
            workflow=workflow,
            steps_execution_plan=steps_execution_plan
        )
        logger.debug(f"Compiled workflow execution plan: {workflow_execution_plan}")
        return workflow_execution_plan
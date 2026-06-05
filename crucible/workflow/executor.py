import logging

from crucible.models import WorkflowExecutionPlan, StepStatus


logger = logging.getLogger(__name__)

class WorkflowExecutor:    
    def run(self, workflow_execution_plan: WorkflowExecutionPlan) -> None:
        data = None
        for step_execution_plan in workflow_execution_plan.steps_execution_plan:
            step = step_execution_plan.step
            config = step_execution_plan.config
            
            try:
                logger.debug(f"Executing step: {step.key} with config: {config}")
                data = step.execute(data)
                step_execution_plan.status = StepStatus.SUCCESS
            except Exception as e:
                step_execution_plan.status = StepStatus.FAILED
                logger.error(f"Step {step.key} failed with error: {e}")
                break

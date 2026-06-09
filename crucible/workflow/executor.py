import logging

from crucible.models import WorkflowExecutionPlan, StepStatus, StepExecutionContext


logger = logging.getLogger(__name__)

class WorkflowExecutor:    
    def run(self, workflow_execution_plan: WorkflowExecutionPlan) -> None:
        data = None
        context = StepExecutionContext()
        for step_execution_plan in workflow_execution_plan.steps_execution_plan:
            step = step_execution_plan.step            
            try:
                logger.info(f"Executing step: {step.name}")
                data = step.execute(data=data, context=context)
                step_execution_plan.status = StepStatus.SUCCESS
            except Exception as e:
                step_execution_plan.status = StepStatus.FAILED
                logger.error(f"Step {step.key} failed with error: {e}")
                raise e

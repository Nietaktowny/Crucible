import logging
from datetime import datetime, UTC

from crucible.models import (
    WorkflowExecutionPlan,
    StepStatus,
    StepExecutionContext,
    FrameContext,
    WorkflowRunResult,
    WorkflowStatus
)

logger = logging.getLogger(__name__)

class WorkflowExecutor:    
    def run(self, workflow_execution_plan: WorkflowExecutionPlan) -> WorkflowRunResult:
        result = WorkflowRunResult(status=WorkflowStatus.RUNNING)
        data: FrameContext | None = None
        context = StepExecutionContext()
        result.statistics.started_at = datetime.now(UTC)
        for step_execution_plan in workflow_execution_plan.steps_execution_plan:
            step = step_execution_plan.step            
            try:
                logger.info(f"Executing step: {step.name}")
                for guard in step.guards():
                    guard.check(data)
                data = step.execute(data=data, context=context)
                step_execution_plan.status = StepStatus.SUCCESS
            except Exception as e:
                step_execution_plan.status = StepStatus.FAILED
                logger.error(f"Step {step.key} failed with error: {e}")
                result.error = e
                result.status = WorkflowStatus.FAILED
                break
            else:
                result.status = WorkflowStatus.SUCCESS
        result.statistics.ended_at = datetime.now(UTC)
        result.statistics.total_time = (result.statistics.ended_at - result.statistics.started_at).total_seconds()
        result.statistics.total_steps = len(workflow_execution_plan.steps_execution_plan)
        result.statistics.system_steps = len([step_plan.step.key for step_plan in workflow_execution_plan.steps_execution_plan if step_plan.step.key.startswith("__")])
        if data is not None:
            result.preview = data.preview
            result.row_count = data.row_count
        return result
        
        

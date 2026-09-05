import logging
from datetime import datetime, UTC

from crucible.models import (
    WorkflowExecutionPlan,
    StepStatus,
    StepExecutionContext,
    FrameContext,
    WorkflowRunResult,
    WorkflowStatus,
    WorkflowErrorContext
)

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    """Workflow execution engine. It's a class that should
    iterate over compiled execution plan and collect results.
    It also is responsible for calling runtime guards.
    
    Responsibilities:
    
    - Running steps and passing steps results between them
    - Preparing run statistics and context information
    - Calling runtime guards defined in steps
    - Returning WorkflowRunResult
    """
     
    def run(self, workflow_execution_plan: WorkflowExecutionPlan) -> WorkflowRunResult:
        """Run the workflow based on workflow execution plan.

        Args:
            workflow_execution_plan (WorkflowExecutionPlan): Compiled workflow execution plan to run.

        Returns:
            WorkflowRunResult: Result of the run packed together with runtime statistics and context.
        """
        result = WorkflowRunResult(name=workflow_execution_plan.workflow.name, status=WorkflowStatus.RUNNING)
        data: FrameContext | None = None
        context = StepExecutionContext()
        result.statistics.started_at = datetime.now(UTC)
        logger.debug(f"Applied optimizations: {workflow_execution_plan.applied_optimizations}")
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
                logger.error(f"Step '{step.key}' with name '{step.name}' failed with error: {e}")
                result.error = WorkflowErrorContext(
                    error=e,
                    step_id=step.id,
                    step_name=step.name,
                    frame_schema=data.schema if data else None
                )
                result.status = WorkflowStatus.FAILED
                break
            else:
                result.status = WorkflowStatus.SUCCESS
        result.statistics.ended_at = datetime.now(UTC)
        result.statistics.total_time = (result.statistics.ended_at - result.statistics.started_at).total_seconds()
        result.statistics.total_steps = len(workflow_execution_plan.steps_execution_plan)
        result.statistics.system_steps = len([step_plan.step.key for step_plan in workflow_execution_plan.steps_execution_plan if step_plan.step.key.startswith("__")])
        if data is not None:
            result.preview = data.preview.to_dicts() if data.preview is not None else None
            result.row_count = data.row_count
        return result
        
        

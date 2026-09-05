from fastapi import APIRouter, Depends

from crucible_server.dependencies import get_run_service, get_workflow_service
from crucible_server.schemas import WorkflowRunRequest, WorkflowRunResponse
from crucible_server.services.runs import WorkflowRunService
from crucible_server.services.workflows import WorkflowService

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/workflows/{workflow_name}", response_model=WorkflowRunResponse)
def run_workflow(
    workflow_name: str,
    request: WorkflowRunRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    run_service: WorkflowRunService = Depends(get_run_service),
) -> WorkflowRunResponse:
    """Compile and execute a stored workflow, then persist and return its result.

    Args:
        workflow_name (str): Name of the workflow to run.
        request (WorkflowRunRequest): Run options (preview limit, plan printing, inspection).
        workflow_service (WorkflowService): Injected workflow service, used to resolve the workflow path.
        run_service (WorkflowRunService): Injected run service that performs the actual execution.

    Returns:
        WorkflowRunResponse: Outcome of the run, including any preview rows and row count.
    """
    return run_service.run_workflow(
        workflow_name=workflow_name,
        workflow_service=workflow_service,
        print_plan=request.print_plan,
        preview_limit=request.preview_limit,
        inspect=request.inspect,
    )

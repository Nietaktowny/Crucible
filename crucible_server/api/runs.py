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
    return run_service.run_workflow(
        workflow_name=workflow_name,
        workflow_service=workflow_service,
        print_plan=request.print_plan,
        preview_limit=request.preview_limit,
        inspect=request.inspect,
    )
from fastapi import APIRouter, Depends, Response, status, HTTPException

from crucible_server.dependencies import get_workflow_service
from crucible_server.schemas import (
    WorkflowCreateRequest,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowUpdateRequest,
)
from crucible_server.services.workflows import WorkflowService
from crucible_server.services.previews import WorkflowPreviewService
from crucible_server.schemas import (
    WorkflowPreviewRequest, WorkflowPreviewResponse, FilterValuesRequest, FilterValuesResponse,
)
from crucible.workflow.evaluation import EvaluationError

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _preview_call(service, operation, request):
    try:
        return getattr(WorkflowPreviewService(service), operation)(request)
    except EvaluationError as exc:
        raise HTTPException(status_code=422, detail={
            "error": "workflow_preview_failed", "message": str(exc),
            "step_id": exc.step_id, "step_name": exc.step_name,
            "workflow_name": exc.workflow_name,
        }) from exc
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail={
            "error": "invalid_preview", "message": str(exc), "step_id": request.step_id,
        }) from exc


@router.post("/{workflow_name}/preview", response_model=WorkflowPreviewResponse)
def preview_workflow(
    workflow_name: str,
    request: WorkflowPreviewRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowPreviewResponse:
    """Preview a draft without saving or executing output steps."""
    return _preview_call(workflow_service, "preview", request)


@router.post("/{workflow_name}/filter-values", response_model=FilterValuesResponse)
def filter_values(
    workflow_name: str,
    request: FilterValuesRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> FilterValuesResponse:
    """Search distinct values across the entire selected-step output."""
    return _preview_call(workflow_service, "filter_values", request)


@router.get("", response_model=WorkflowListResponse)
def list_workflows(
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowListResponse:
    """List all workflows stored on the server.

    Args:
        workflow_service (WorkflowService): Injected workflow service.

    Returns:
        WorkflowListResponse: Name and path of every stored workflow.
    """
    return WorkflowListResponse(
        workflows=workflow_service.list_workflows(),
    )


@router.get("/{workflow_name}", response_model=WorkflowResponse)
def get_workflow(
    workflow_name: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """Fetch one workflow's parsed definition.

    Args:
        workflow_name (str): Name of the workflow to fetch.
        workflow_service (WorkflowService): Injected workflow service.

    Returns:
        WorkflowResponse: Name, path and parsed content of the workflow.
    """
    return workflow_service.get_workflow(workflow_name)


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    request: WorkflowCreateRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """Create a new workflow from raw YAML content.

    Args:
        request (WorkflowCreateRequest): Name and YAML content for the new workflow.
        workflow_service (WorkflowService): Injected workflow service.

    Returns:
        WorkflowResponse: The newly created workflow.
    """
    return workflow_service.create_workflow(
        name=request.name,
        content=request.content,
    )


@router.put("/{workflow_name}", response_model=WorkflowResponse)
def update_workflow(
    workflow_name: str,
    request: WorkflowUpdateRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    """Overwrite an existing workflow's YAML content.

    Args:
        workflow_name (str): Name of the workflow to update.
        request (WorkflowUpdateRequest): New YAML content.
        workflow_service (WorkflowService): Injected workflow service.

    Returns:
        WorkflowResponse: The updated workflow.
    """
    return workflow_service.update_workflow(
        name=workflow_name,
        content=request.content,
    )


@router.delete("/{workflow_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    workflow_name: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> Response:
    """Delete a workflow permanently.

    Args:
        workflow_name (str): Name of the workflow to delete.
        workflow_service (WorkflowService): Injected workflow service.

    Returns:
        Response: An empty `204 No Content` response.
    """
    workflow_service.delete_workflow(workflow_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

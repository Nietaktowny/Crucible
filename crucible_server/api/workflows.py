from fastapi import APIRouter, Depends, Response, status

from crucible_server.dependencies import get_workflow_service
from crucible_server.schemas import (
    WorkflowCreateRequest,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowUpdateRequest,
)
from crucible_server.services.workflows import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


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

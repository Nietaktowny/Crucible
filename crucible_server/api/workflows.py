# src/crucible_server/api/workflows.py

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
    return WorkflowListResponse(
        workflows=workflow_service.list_workflows(),
    )


@router.get("/{workflow_name}", response_model=WorkflowResponse)
def get_workflow(
    workflow_name: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    return workflow_service.get_workflow(workflow_name)


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    request: WorkflowCreateRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
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
    return workflow_service.update_workflow(
        name=workflow_name,
        content=request.content,
    )


@router.delete("/{workflow_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    workflow_name: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> Response:
    workflow_service.delete_workflow(workflow_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
from fastapi import APIRouter, Depends, HTTPException

from crucible_server.dependencies import get_workflow_service
from crucible_server.services.workflows import WorkflowService
from crucible_workspace import CachedPreview
from crucible import WorkflowRunResult

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/workflows/{workflow_name}/preview", response_model=CachedPreview)
def get_cached_preview(
    workflow_name: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> CachedPreview:
    preview = workflow_service.get_cached_preview(workflow_name)

    if preview is None:
        raise HTTPException(
            status_code=404,
            detail=f"Cached preview not found for workflow '{workflow_name}'.",
        )

    return preview

@router.get("/runs", response_model=list[WorkflowRunResult])
def get_all_runs(
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowRunResult]:
    return workflow_service.db.get_all_results()
from typing import Any
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
import pandas as pd

from crucible_server.dependencies import get_workflow_service
from crucible_server.services.workflows import WorkflowService
from crucible_server.schemas import ExcelSheetsRequest
from crucible_workspace import CachedPreview
from crucible import WorkflowRunResult, get_steps_schema

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/workflows/{workflow_name}/preview", response_model=CachedPreview)
def get_cached_preview(
    workflow_name: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> CachedPreview:
    """Return the last cached preview for a workflow, if one exists.

    The preview is cached per exact workflow YAML text, so it goes stale
    (and this endpoint 404s) as soon as the workflow is edited and not
    re-run.

    Args:
        workflow_name (str): Name of the workflow to fetch a preview for.
        workflow_service (WorkflowService): Injected workflow service.

    Returns:
        CachedPreview: The cached preview rows, schema and row count.

    Raises:
        HTTPException: 404 if no cached preview exists for this workflow's current content.
    """
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
    """List every recorded workflow run, across all workflows.

    Args:
        workflow_service (WorkflowService): Injected workflow service.

    Returns:
        list[WorkflowRunResult]: All stored run results, most recent first.
    """
    return workflow_service.db.get_all_results()


@router.get("/steps_schema", response_model=list[dict[str, Any]])
def get_all_steps_schema() -> list[dict[str, Any]]:
    """Return the JSON Schema for every registered step's configuration.

    Consumed by `crucible_gui` to render step configuration forms
    dynamically, without hardcoding each step's fields on the frontend.

    Returns:
        list[dict[str, Any]]: One JSON Schema document per registered step.
    """
    return get_steps_schema()

@router.post(
    "/files/sheets",
    response_model=list[str],
)
def get_excel_file_sheets(
    request: ExcelSheetsRequest,
) -> list[str]:
    """List the sheet names available in an Excel workbook.

    Used to populate the sheet picker for the "Read Excel"/"Write Excel"
    steps, given the path the user has already entered.

    Args:
        request (ExcelSheetsRequest): Path to the Excel file to inspect.

    Returns:
        list[str]: Sheet names in the workbook, in file order.

    Raises:
        HTTPException: 404 if the path does not point to an existing file,
            422 if the file cannot be read as an Excel workbook.
    """
    path = Path(request.path)

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {path}",
        )

    try:
        with pd.ExcelFile(path) as file:
            return list(file.sheet_names)
    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail=f"Could not read Excel file: {error}",
        ) from error

# src/crucible_server/schemas.py

from pydantic import BaseModel, Field
from typing import Any

from crucible.models import (
    Workflow
)


class WorkflowSummary(BaseModel):
    """Lightweight workflow listing entry (no parsed content)."""

    name: str
    """Workflow name, as used in API paths and the on-disk filename."""

    path: str
    """Absolute path to the workflow's YAML file on the server."""


class WorkflowListResponse(BaseModel):
    """Response body for `GET /workflows`."""

    workflows: list[WorkflowSummary]
    """All workflows currently stored on the server."""


class WorkflowCreateRequest(BaseModel):
    """Request body for `POST /workflows`."""

    name: str = Field(min_length=1)
    """Name for the new workflow. Must be unique and filesystem-safe."""

    content: str = Field(min_length=1)
    """Raw YAML text defining the workflow."""


class WorkflowUpdateRequest(BaseModel):
    """Request body for `PUT /workflows/{workflow_name}`."""

    content: str = Field(min_length=1)
    """Raw YAML text to overwrite the existing workflow with."""


class WorkflowResponse(BaseModel):
    """Response body returned by the workflow list/create/update/get endpoints."""

    name: str
    """Workflow name."""

    path: str
    """Absolute path to the workflow's YAML file on the server."""

    content: Workflow
    """Parsed workflow definition (name and ordered step configs)."""

class WorkflowRunRequest(BaseModel):
    """Request body for `POST /runs/workflows/{workflow_name}`."""

    print_plan: bool = False
    """If true, pretty-print the compiled execution plan to the server console."""

    preview_limit: int = 200
    """Maximum number of output rows to collect for the run's preview."""

    inspect: bool = True
    """If true, append an inspection step that captures the final preview/row count."""

class WorkflowRunResponse(BaseModel):
    """Response body for a completed workflow run."""

    workflow_name: str
    """Name of the workflow that was run."""

    success: bool
    """Whether the run completed without error."""

    message: str
    """Human-readable summary of the run outcome."""

    preview: list[dict[str, Any]] | None = None
    """Preview rows collected from the final frame, if any were captured."""

    row_count: int | None = None
    """Total row count of the final frame, if known."""

class ExcelSheetsRequest(BaseModel):
    """Request body for `POST /data/files/sheets`."""

    path: str
    """Path to the Excel file to inspect, on the machine running the server."""

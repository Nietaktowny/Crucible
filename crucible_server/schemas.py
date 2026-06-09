# src/crucible_server/schemas.py

from pydantic import BaseModel, Field


class WorkflowSummary(BaseModel):
    name: str
    path: str


class WorkflowListResponse(BaseModel):
    workflows: list[WorkflowSummary]


class WorkflowCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    content: str = Field(min_length=1)


class WorkflowUpdateRequest(BaseModel):
    content: str = Field(min_length=1)


class WorkflowResponse(BaseModel):
    name: str
    path: str
    content: str

class WorkflowRunRequest(BaseModel):
    print_plan: bool = False


class WorkflowRunResponse(BaseModel):
    workflow_name: str
    success: bool
    message: str
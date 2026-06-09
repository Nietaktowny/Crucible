# src/crucible_server/dependencies.py

from functools import lru_cache

from crucible_server.services.runs import WorkflowRunService
from crucible_server.services.workflows import WorkflowService


@lru_cache
def get_workflow_service() -> WorkflowService:
    return WorkflowService()


@lru_cache
def get_run_service() -> WorkflowRunService:
    return WorkflowRunService()
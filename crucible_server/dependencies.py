# src/crucible_server/dependencies.py

from functools import lru_cache

from crucible_server.services.runs import WorkflowRunService
from crucible_server.services.workflows import WorkflowService


@lru_cache
def get_workflow_service() -> WorkflowService:
    """Return the process-wide `WorkflowService` singleton.

    Cached with `lru_cache` so every request handler shares the same service
    instance (and therefore the same underlying `WorkflowStore` and
    `PreviewCache`) for the lifetime of the server process.

    Returns:
        WorkflowService: Shared workflow service instance.
    """
    return WorkflowService()


@lru_cache
def get_run_service() -> WorkflowRunService:
    """Return the process-wide `WorkflowRunService` singleton.

    Returns:
        WorkflowRunService: Shared workflow run service instance.
    """
    return WorkflowRunService()

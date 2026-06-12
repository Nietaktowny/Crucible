# src/crucible_server/errors.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class InvalidWorkflowNameError(Exception):
    pass


class WorkflowNotFoundError(Exception):
    def __init__(self, workflow_name: str) -> None:
        self.workflow_name = workflow_name
        super().__init__(f"Workflow not found: {workflow_name}")


class WorkflowAlreadyExistsError(Exception):
    def __init__(self, workflow_name: str) -> None:
        self.workflow_name = workflow_name
        super().__init__(f"Workflow already exists: {workflow_name}")


class WorkflowRunError(Exception):
    def __init__(self, workflow_name: str, step_name: str, reason: str) -> None:
        self.workflow_name = workflow_name
        self.reason = reason
        super().__init__(f"Workflow run failed: {workflow_name}:{step_name} - {reason}")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(InvalidWorkflowNameError)
    async def invalid_workflow_name_handler(
        request: Request,
        exc: InvalidWorkflowNameError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_workflow_name",
                "message": str(exc),
            },
        )

    @app.exception_handler(WorkflowNotFoundError)
    async def workflow_not_found_handler(
        request: Request,
        exc: WorkflowNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "error": "workflow_not_found",
                "message": str(exc),
                "workflow_name": exc.workflow_name,
            },
        )

    @app.exception_handler(WorkflowAlreadyExistsError)
    async def workflow_exists_handler(
        request: Request,
        exc: WorkflowAlreadyExistsError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "error": "workflow_already_exists",
                "message": str(exc),
                "workflow_name": exc.workflow_name,
            },
        )

    @app.exception_handler(WorkflowRunError)
    async def workflow_run_error_handler(
        request: Request,
        exc: WorkflowRunError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": "workflow_run_failed",
                "message": str(exc),
                "workflow_name": exc.workflow_name,
                "reason": exc.reason,
            },
        )
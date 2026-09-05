# src/crucible_server/errors.py

import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from crucible.models import WorkflowErrorContext


class InvalidWorkflowNameError(Exception):
    """Raised when a workflow name fails the store's naming rules."""

    pass


class WorkflowNotFoundError(Exception):
    """Raised when a requested workflow does not exist in the store."""

    def __init__(self, workflow_name: str) -> None:
        self.workflow_name = workflow_name
        super().__init__(f"Workflow not found: {workflow_name}")


class WorkflowAlreadyExistsError(Exception):
    """Raised when creating a workflow whose name is already taken."""

    def __init__(self, workflow_name: str) -> None:
        self.workflow_name = workflow_name
        super().__init__(f"Workflow already exists: {workflow_name}")


class WorkflowRunError(Exception):
    """Raised when a workflow run fails during execution.

    Wraps the underlying step failure with the workflow name and the full
    error context (step, frame schema, and formatted traceback) so API
    responses can point the caller at exactly where and why execution
    stopped.
    """

    def __init__(self, workflow_name: str, error_context: WorkflowErrorContext) -> None:
        self.workflow_name = workflow_name
        self.error_context = error_context
        super().__init__(
            f"Workflow run failed: {workflow_name}:{error_context.step_name} - {error_context.error}"
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register JSON error handlers for the domain exceptions above.

    Each handler translates an internal exception into a stable JSON error
    shape (`error`, `message`, plus any exception-specific fields) with an
    appropriate HTTP status code, so API consumers never see a raw Python
    traceback for these expected failure modes.

    Args:
        app (FastAPI): Application instance to attach the handlers to.
    """
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
        context = exc.error_context

        return JSONResponse(
            status_code=500,
            content={
                "error": "workflow_run_failed",
                "message": str(exc),
                "workflow_name": exc.workflow_name,
                "step_id": context.step_id,
                "step_name": context.step_name,
                "frame_schema": context.frame_schema,
                "traceback": context.model_dump(mode="json")["error"],
            },
        )

class UnhandledErrorMiddleware(BaseHTTPMiddleware):
    """Turns any exception no domain handler recognizes into a JSON 500.

    Registering a handler for the bare `Exception` type via
    `@app.exception_handler` would *not* fix this: Starlette special-cases
    that handler into the outermost `ServerErrorMiddleware`, which sits
    *outside* `CORSMiddleware`, so its response is sent without CORS
    headers — browsers then report a blocked cross-origin request instead
    of the actual server error. This middleware must be added to the app
    *before* `CORSMiddleware` (Starlette's `add_middleware` prepends, so
    the last one added ends up outermost — adding this one first nests it
    inside `CORSMiddleware`) and catches the exception itself, letting
    `CORSMiddleware` see a normal response and add its headers as usual.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> JSONResponse:
        try:
            return await call_next(request)
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "message": str(exc) or exc.__class__.__name__,
                    "traceback": "".join(traceback.format_exception(exc)),
                },
            )

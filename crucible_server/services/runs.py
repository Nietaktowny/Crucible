from crucible import run_workflow

from crucible_server.errors import WorkflowRunError
from crucible_server.schemas import WorkflowRunResponse
from crucible_server.services.workflows import WorkflowService


class WorkflowRunService:
    """Executes stored workflows and turns their result into an API response."""

    def run_workflow(
        self,
        workflow_name: str,
        workflow_service: WorkflowService,
        print_plan: bool = False,
        preview_limit: int = 200,
        inspect: bool = True,
    ) -> WorkflowRunResponse:
        """Load, compile and run a workflow by name.

        On success, the result is recorded to the runtime database and, if
        a preview was collected, cached against the workflow's current
        content. On failure, the run is still recorded before the error is
        raised, so failed runs remain visible in run history.

        Args:
            workflow_name (str): Name of the workflow to run.
            workflow_service (WorkflowService): Service used to resolve the workflow's
                path, cache its preview, and persist the run result.
            print_plan (bool, optional): If true, pretty-print the compiled execution plan. Defaults to False.
            preview_limit (int, optional): Maximum number of preview rows to collect. Defaults to 200.
            inspect (bool, optional): If true, append an inspection step to capture the final preview/row count. Defaults to True.

        Returns:
            WorkflowRunResponse: Outcome of the run, including any preview rows and row count.

        Raises:
            WorkflowRunError: If the workflow failed during execution. The
                original exception is chained via `from result.error.error`.
        """
        workflow_path = workflow_service.get_workflow_path(workflow_name)

        result = run_workflow(
            workflow_path=workflow_path,
            print_plan=print_plan,
            preview_limit=preview_limit,
            inspect=inspect,
        )

        workflow_service.store_run_result(result)

        if result.error is not None:
            raise WorkflowRunError(
                workflow_name=workflow_name,
                error_context=result.error,
            ) from result.error.error

        if result.preview is not None:
            workflow_service.cache_preview(
                workflow_name=workflow_name,
                preview=result.preview,
                row_count=result.row_count or 0,
                preview_limit=preview_limit,
            )

        return WorkflowRunResponse(
            workflow_name=workflow_name,
            success=True,
            message="Workflow finished successfully.",
            preview=result.preview,
            row_count=result.row_count,
        )

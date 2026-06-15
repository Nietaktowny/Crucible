from crucible import run_workflow

from crucible_server.errors import WorkflowRunError
from crucible_server.schemas import WorkflowRunResponse
from crucible_server.services.workflows import WorkflowService


class WorkflowRunService:
    def run_workflow(
        self,
        workflow_name: str,
        workflow_service: WorkflowService,
        print_plan: bool = False,
        preview_limit: int = 200,
        inspect: bool = True,
    ) -> WorkflowRunResponse:
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
                step_name=result.error.step_name,
                reason=str(result.error.error),
            ) from result.error.error

        preview = (
            result.preview.to_dicts()
            if result.preview is not None
            else None
        )

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
            preview=preview,
            row_count=result.row_count,
        )
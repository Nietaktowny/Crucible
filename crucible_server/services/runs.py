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
    ) -> WorkflowRunResponse:
        workflow_path = workflow_service.get_workflow_path(workflow_name)

        try:
            run_workflow(
                workflow_path=workflow_path,
                print_plan=print_plan,
            )
        except Exception as exc:
            raise WorkflowRunError(
                workflow_name=workflow_name,
                reason=str(exc),
            ) from exc

        return WorkflowRunResponse(
            workflow_name=workflow_name,
            success=True,
            message="Workflow finished successfully.",
        )
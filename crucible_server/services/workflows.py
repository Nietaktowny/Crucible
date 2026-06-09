# src/crucible_server/services/workflows.py

from pathlib import Path

from crucible_workspace import WorkflowStore
from crucible_workspace.exceptions import (
    InvalidWorkflowNameError as WorkspaceInvalidWorkflowNameError,
    WorkflowAlreadyExistsError as WorkspaceWorkflowAlreadyExistsError,
    WorkflowNotFoundError as WorkspaceWorkflowNotFoundError,
)

from crucible_server.errors import (
    InvalidWorkflowNameError,
    WorkflowAlreadyExistsError,
    WorkflowNotFoundError,
)
from crucible_server.schemas import WorkflowResponse, WorkflowSummary


class WorkflowService:
    def __init__(self) -> None:
        self.store = WorkflowStore()

    def list_workflows(self) -> list[WorkflowSummary]:
        return [
            WorkflowSummary(
                name=item.name,
                path=str(item.path),
            )
            for item in self.store.list_workflows()
        ]

    def get_workflow(self, name: str) -> WorkflowResponse:
        try:
            content = self.store.read_workflow(name)
            path = self.store.get_workflow_path(name)
        except WorkspaceWorkflowNotFoundError as exc:
            raise WorkflowNotFoundError(name) from exc
        except WorkspaceInvalidWorkflowNameError as exc:
            raise InvalidWorkflowNameError(str(exc)) from exc

        return WorkflowResponse(
            name=name,
            path=str(path),
            content=content,
        )

    def create_workflow(self, name: str, content: str) -> WorkflowResponse:
        try:
            info = self.store.create_workflow(name=name, content=content)
        except WorkspaceWorkflowAlreadyExistsError as exc:
            raise WorkflowAlreadyExistsError(name) from exc
        except WorkspaceInvalidWorkflowNameError as exc:
            raise InvalidWorkflowNameError(str(exc)) from exc

        return WorkflowResponse(
            name=info.name,
            path=str(info.path),
            content=content,
        )

    def update_workflow(self, name: str, content: str) -> WorkflowResponse:
        try:
            info = self.store.update_workflow(name=name, content=content)
        except WorkspaceWorkflowNotFoundError as exc:
            raise WorkflowNotFoundError(name) from exc
        except WorkspaceInvalidWorkflowNameError as exc:
            raise InvalidWorkflowNameError(str(exc)) from exc

        return WorkflowResponse(
            name=info.name,
            path=str(info.path),
            content=content,
        )

    def delete_workflow(self, name: str) -> None:
        try:
            self.store.delete_workflow(name)
        except WorkspaceWorkflowNotFoundError as exc:
            raise WorkflowNotFoundError(name) from exc
        except WorkspaceInvalidWorkflowNameError as exc:
            raise InvalidWorkflowNameError(str(exc)) from exc

    def get_workflow_path(self, name: str) -> Path:
        try:
            return self.store._get_existing_workflow_path(name)
        except WorkspaceWorkflowNotFoundError as exc:
            raise WorkflowNotFoundError(name) from exc
        except WorkspaceInvalidWorkflowNameError as exc:
            raise InvalidWorkflowNameError(str(exc)) from exc
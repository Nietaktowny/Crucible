import re
from pathlib import Path

from crucible_workspace.exceptions import (
    InvalidWorkflowNameError,
    WorkflowAlreadyExistsError,
    WorkflowNotFoundError,
)
from crucible_workspace.models import WorkflowInfo
from crucible_workspace.paths import get_workflows_dir


_VALID_WORKFLOW_NAME = re.compile(r"^[a-zA-Z0-9_.-]+$")

class WorkflowStore:
    def __init__(self, workflows_dir: Path | None = None) -> None:
        self.workflows_dir = workflows_dir or get_workflows_dir()
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

    def list_workflows(self) -> list[WorkflowInfo]:
        files = sorted(self.workflows_dir.glob("*.yaml"))

        return [
            WorkflowInfo(
                name=file.stem,
                path=file,
            )
            for file in files
        ]

    def create_workflow(self, name: str, content: str) -> WorkflowInfo:
        path = self._get_workflow_path(name)

        if path.exists():
            raise WorkflowAlreadyExistsError(f"Workflow already exists: {name}")

        path.write_text(content, encoding="utf-8")

        return WorkflowInfo(name=name, path=path)

    def read_workflow(self, name: str) -> str:
        path = self._get_existing_workflow_path(name)
        return path.read_text(encoding="utf-8")

    def update_workflow(self, name: str, content: str) -> WorkflowInfo:
        path = self._get_existing_workflow_path(name)
        path.write_text(content, encoding="utf-8")

        return WorkflowInfo(name=name, path=path)

    def delete_workflow(self, name: str) -> None:
        path = self._get_existing_workflow_path(name)
        path.unlink()

    def workflow_exists(self, name: str) -> bool:
        return self._get_workflow_path(name).exists()

    def _get_existing_workflow_path(self, name: str) -> Path:
        path = self._get_workflow_path(name)

        if not path.exists():
            raise WorkflowNotFoundError(f"Workflow not found: {name}")

        return path

    def _get_workflow_path(self, name: str) -> Path:
        self._validate_workflow_name(name)
        return self.workflows_dir / f"{name}.yaml"

    @staticmethod
    def _validate_workflow_name(name: str) -> None:
        if not name:
            raise InvalidWorkflowNameError("Workflow name cannot be empty")

        if not _VALID_WORKFLOW_NAME.match(name):
            raise InvalidWorkflowNameError(
                "Workflow name may contain only letters, numbers, dots, underscores and dashes"
            )
            
    def get_workflow_info(self, name: str) -> WorkflowInfo:
        path = self._get_existing_workflow_path(name)
        return WorkflowInfo(name=name, path=path)

    def get_workflow_path(self, name: str) -> Path:
        return self._get_existing_workflow_path(name)
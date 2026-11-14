import re
import os
import stat
from pathlib import Path
from tempfile import NamedTemporaryFile

import yaml
from pydantic import ValidationError

from crucible_workspace.exceptions import (
    InvalidWorkflowNameError,
    InvalidWorkflowContentError,
    WorkflowAlreadyExistsError,
    WorkflowNotFoundError,
)
from crucible_workspace.models import WorkflowInfo
from crucible_workspace.paths import get_workflows_dir

from crucible.workflow import (
    WorkflowLoader
)
from crucible.models import (
    Workflow
)


_VALID_WORKFLOW_NAME = re.compile(r"^[a-zA-Z0-9_.-]+$")

class WorkflowStore:
    """Filesystem CRUD for workflow YAML files.

    Each workflow is a single `<name>.yaml` file under `workflows_dir`
    (by default `crucible_workspace.paths.get_workflows_dir()`). The store
    preserves raw YAML text and validates its workflow structure before any
    write. Loading stored definitions is delegated to `WorkflowLoader`.
    """

    def __init__(self, workflows_dir: Path | None = None) -> None:
        self.workflows_dir = workflows_dir or get_workflows_dir()
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self._models_loader = WorkflowLoader()

    def list_workflows(self) -> list[WorkflowInfo]:
        """List all workflows in `workflows_dir`, sorted by filename.

        Returns:
            list[WorkflowInfo]: Name and path of every `*.yaml` file found.
        """
        files = sorted(self.workflows_dir.glob("*.yaml"))

        return [
            WorkflowInfo(
                name=file.stem,
                path=file,
            )
            for file in files
        ]

    def create_workflow(self, name: str, content: str) -> WorkflowInfo:
        """Create a new workflow file.

        Args:
            name (str): Name for the new workflow; must be unique and match the naming rules.
            content (str): Raw YAML text to write.

        Returns:
            WorkflowInfo: Name and path of the newly created file.

        Raises:
            WorkflowAlreadyExistsError: If a file for this name already exists.
            InvalidWorkflowNameError: If `name` fails the naming rules.
            InvalidWorkflowContentError: If YAML syntax or workflow structure is invalid.
        """
        path = self._get_workflow_path(name)

        if path.exists():
            raise WorkflowAlreadyExistsError(f"Workflow already exists: {name}")

        self._validate_content(content)
        self._write_atomic(path, content, create=True)

        return WorkflowInfo(name=name, path=path)

    def read_workflow(self, name: str) -> str:
        """Read a workflow file's raw YAML text.

        Args:
            name (str): Name of the workflow to read.

        Returns:
            str: Raw YAML text of the workflow file.

        Raises:
            WorkflowNotFoundError: If no file exists for this name.
            InvalidWorkflowNameError: If `name` fails the naming rules.
        """
        path = self._get_existing_workflow_path(name)
        return path.read_text(encoding="utf-8")

    def update_workflow(self, name: str, content: str) -> WorkflowInfo:
        """Validate and atomically replace an existing workflow file's content.

        Args:
            name (str): Name of the workflow to update.
            content (str): New raw YAML text.

        Returns:
            WorkflowInfo: Name and path of the updated file.

        Raises:
            WorkflowNotFoundError: If no file exists for this name.
            InvalidWorkflowNameError: If `name` fails the naming rules.
            InvalidWorkflowContentError: If YAML syntax or workflow structure is invalid.
        """
        path = self._get_existing_workflow_path(name)
        self._validate_content(content)
        self._write_atomic(path, content)

        return WorkflowInfo(name=name, path=path)

    @staticmethod
    def _validate_content(content: str) -> None:
        """Validate syntax and workflow shape without executing step configs."""
        try:
            raw = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise InvalidWorkflowContentError(f"Invalid workflow YAML: {exc}") from exc
        try:
            Workflow.model_validate(raw)
        except ValidationError as exc:
            raise InvalidWorkflowContentError(f"Invalid workflow definition: {exc}") from exc

    @staticmethod
    def _write_atomic(path: Path, content: str, *, create: bool = False) -> None:
        """Publish a complete file, preserving the old file on write failures."""
        temporary_path = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                if not create:
                    os.chmod(temporary_path, stat.S_IMODE(path.stat().st_mode))
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
            if create:
                # Hard-link publication is atomic and cannot overwrite a file
                # concurrently created after the initial existence check.
                try:
                    os.link(temporary_path, path)
                except FileExistsError as exc:
                    raise WorkflowAlreadyExistsError(f"Workflow already exists: {path.stem}") from exc
            else:
                os.replace(temporary_path, path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def delete_workflow(self, name: str) -> None:
        """Delete a workflow file.

        Args:
            name (str): Name of the workflow to delete.

        Raises:
            WorkflowNotFoundError: If no file exists for this name.
            InvalidWorkflowNameError: If `name` fails the naming rules.
        """
        path = self._get_existing_workflow_path(name)
        path.unlink()

    def workflow_exists(self, name: str) -> bool:
        """Check whether a workflow file exists for this name.

        Args:
            name (str): Workflow name to check.

        Returns:
            bool: `True` if the file exists.

        Raises:
            InvalidWorkflowNameError: If `name` fails the naming rules.
        """
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
        """Resolve a workflow name to its `WorkflowInfo` without reading its content.

        Args:
            name (str): Name of the workflow to look up.

        Returns:
            WorkflowInfo: Name and path of the workflow.

        Raises:
            WorkflowNotFoundError: If no file exists for this name.
            InvalidWorkflowNameError: If `name` fails the naming rules.
        """
        path = self._get_existing_workflow_path(name)
        return WorkflowInfo(name=name, path=path)

    def get_workflow_path(self, name: str) -> Path:
        """Resolve a workflow name to its on-disk YAML file path.

        Args:
            name (str): Name of the workflow to look up.

        Returns:
            Path: Absolute path to the workflow's YAML file.

        Raises:
            WorkflowNotFoundError: If no file exists for this name.
            InvalidWorkflowNameError: If `name` fails the naming rules.
        """
        return self._get_existing_workflow_path(name)

    def get_workflow_model(self, name: str) -> Workflow:
        """Load and parse a workflow file into a `Workflow` model.

        Args:
            name (str): Name of the workflow to load.

        Returns:
            Workflow: Parsed workflow definition.

        Raises:
            WorkflowNotFoundError: If no file exists for this name.
            InvalidWorkflowNameError: If `name` fails the naming rules.
        """
        workflow = self.get_workflow_path(name)
        return self._models_loader.load(workflow)

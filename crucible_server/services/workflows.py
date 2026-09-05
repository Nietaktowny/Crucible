from pathlib import Path
from typing import Any

from crucible_workspace import WorkflowStore, RuntimeDataStorage, PreviewCache, CachedPreview
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
from crucible.models import WorkflowRunResult

class WorkflowService:
    """Application-level facade over workflow storage and preview caching.

    Bridges `crucible_workspace`'s filesystem-backed `WorkflowStore`,
    `RuntimeDataStorage` and `PreviewCache` to the API layer, translating
    workspace-level exceptions into the server's own error types and
    building the response schemas the routers return.
    """

    def __init__(self) -> None:
        self.store = WorkflowStore()
        self.db = RuntimeDataStorage()
        self.cache = PreviewCache()

    def list_workflows(self) -> list[WorkflowSummary]:
        """List all workflows in the store.

        Returns:
            list[WorkflowSummary]: Name and path of every stored workflow.
        """
        return [
            WorkflowSummary(
                name=item.name,
                path=str(item.path),
            )
            for item in self.store.list_workflows()
        ]

    def get_workflow(self, name: str) -> WorkflowResponse:
        """Load and parse one workflow by name.

        Args:
            name (str): Workflow name.

        Returns:
            WorkflowResponse: Name, path and parsed content of the workflow.

        Raises:
            WorkflowNotFoundError: If no workflow with this name exists.
            InvalidWorkflowNameError: If `name` fails the store's naming rules.
        """
        try:
            content = self.store.get_workflow_model(name)
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
        """Create a new workflow file from raw YAML text.

        Args:
            name (str): Name for the new workflow. Must not already exist.
            content (str): Raw YAML text defining the workflow.

        Returns:
            WorkflowResponse: The newly created workflow, with parsed content.

        Raises:
            WorkflowAlreadyExistsError: If a workflow with this name already exists.
            InvalidWorkflowNameError: If `name` fails the store's naming rules.
        """
        try:
            info = self.store.create_workflow(name=name, content=content)
        except WorkspaceWorkflowAlreadyExistsError as exc:
            raise WorkflowAlreadyExistsError(name) from exc
        except WorkspaceInvalidWorkflowNameError as exc:
            raise InvalidWorkflowNameError(str(exc)) from exc

        return WorkflowResponse(
            name=info.name,
            path=str(info.path),
            content=self.store.get_workflow_model(name),
        )

    def update_workflow(self, name: str, content: str) -> WorkflowResponse:
        """Overwrite an existing workflow's YAML content.

        Args:
            name (str): Name of the workflow to update.
            content (str): New raw YAML text.

        Returns:
            WorkflowResponse: The updated workflow, with re-parsed content.

        Raises:
            WorkflowNotFoundError: If no workflow with this name exists.
            InvalidWorkflowNameError: If `name` fails the store's naming rules.
        """
        try:
            info = self.store.update_workflow(name=name, content=content)
        except WorkspaceWorkflowNotFoundError as exc:
            raise WorkflowNotFoundError(name) from exc
        except WorkspaceInvalidWorkflowNameError as exc:
            raise InvalidWorkflowNameError(str(exc)) from exc
        return WorkflowResponse(
            name=info.name,
            path=str(info.path),
            content=self.store.get_workflow_model(name),
        )

    def delete_workflow(self, name: str) -> None:
        """Permanently delete a workflow's file.

        Args:
            name (str): Name of the workflow to delete.

        Raises:
            WorkflowNotFoundError: If no workflow with this name exists.
            InvalidWorkflowNameError: If `name` fails the store's naming rules.
        """
        try:
            self.store.delete_workflow(name)
        except WorkspaceWorkflowNotFoundError as exc:
            raise WorkflowNotFoundError(name) from exc
        except WorkspaceInvalidWorkflowNameError as exc:
            raise InvalidWorkflowNameError(str(exc)) from exc

    def get_workflow_path(self, name: str) -> Path:
        """Resolve a workflow name to its on-disk YAML file path.

        Args:
            name (str): Workflow name.

        Returns:
            Path: Absolute path to the workflow's YAML file.

        Raises:
            WorkflowNotFoundError: If no workflow with this name exists.
            InvalidWorkflowNameError: If `name` fails the store's naming rules.
        """
        try:
            return self.store._get_existing_workflow_path(name)
        except WorkspaceWorkflowNotFoundError as exc:
            raise WorkflowNotFoundError(name) from exc
        except WorkspaceInvalidWorkflowNameError as exc:
            raise InvalidWorkflowNameError(str(exc)) from exc

    def cache_preview(
        self,
        workflow_name: str,
        preview: list[dict[str, Any]],
        row_count: int = 0,
        preview_limit: int = 200,
    ) -> str:
        """Cache a run's preview rows, keyed by the workflow's raw YAML text.

        The raw text (rather than the parsed model) is used as the cache
        key so any edit to the workflow — even one that doesn't change its
        parsed structure — invalidates the previous preview.

        Args:
            workflow_name (str): Name of the workflow the preview belongs to.
            preview (list[dict[str, Any]]): Preview rows to cache.
            row_count (int, optional): Total row count of the run's output. Defaults to 0.
            preview_limit (int, optional): Row cap that was applied when collecting the preview. Defaults to 200.

        Returns:
            str: Hash of the workflow text used as the cache key.
        """
        # Use raw YAML text as cache key for consistency
        raw_workflow_text = self.store.read_workflow(workflow_name)

        return self.cache.save_preview(
            raw_workflow_text=raw_workflow_text,
            preview=preview,
            row_count=row_count,
            preview_limit=preview_limit,
        )

    def get_cached_preview(self, workflow_name: str) -> CachedPreview | None:
        """Fetch the cached preview matching a workflow's current YAML text.

        Args:
            workflow_name (str): Name of the workflow to fetch a preview for.

        Returns:
            CachedPreview | None: The cached preview, or `None` if the
                workflow has never been run or has changed since its last run.
        """
        # Use raw YAML text as cache key for consistency
        raw_workflow_text = self.store.read_workflow(workflow_name)
        return self.cache.get_preview(raw_workflow_text)

    def store_run_result(self, result: WorkflowRunResult):
        """Persist a workflow run result to the runtime database.

        Args:
            result (WorkflowRunResult): Run result to store.
        """
        self.db.add_result(result)

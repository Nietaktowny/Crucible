class WorkspaceError(Exception):
    """Base class for all `crucible_workspace` errors."""

    pass
class WorkflowNotFoundError(WorkspaceError):
    """Raised when a workflow name does not match any stored workflow file."""

    pass
class WorkflowAlreadyExistsError(WorkspaceError):
    """Raised when creating a workflow whose file already exists."""

    pass
class InvalidWorkflowNameError(WorkspaceError):
    """Raised when a workflow name fails `WorkflowStore`'s naming rules."""

    pass


class InvalidWorkflowContentError(WorkspaceError):
    """Raised when incoming YAML cannot be parsed as a workflow definition."""

    pass

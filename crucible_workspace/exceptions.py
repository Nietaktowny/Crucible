class WorkspaceError(Exception):
    pass
class WorkflowNotFoundError(WorkspaceError):
    pass
class WorkflowAlreadyExistsError(WorkspaceError):
    pass
class InvalidWorkflowNameError(WorkspaceError):
    pass
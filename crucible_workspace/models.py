from pathlib import Path
from pydantic import BaseModel

class WorkflowInfo(BaseModel):
    """Identity of a stored workflow: its name and on-disk YAML path."""

    name: str
    path: Path
class WorkflowCreate(BaseModel):
    """Payload used internally when creating a new workflow file."""

    name: str
    content: str
class WorkflowUpdate(BaseModel):
    """Payload used internally when overwriting a workflow file."""

    content: str

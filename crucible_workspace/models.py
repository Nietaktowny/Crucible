from pathlib import Path
from pydantic import BaseModel

class WorkflowInfo(BaseModel):
    name: str
    path: Path
class WorkflowCreate(BaseModel):
    name: str
    content: str
class WorkflowUpdate(BaseModel):
    content: str
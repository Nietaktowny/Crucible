"""
Local, filesystem-backed storage for Crucible workflows and run data.

This package is independent of the `crucible` execution engine: it owns
where workflow YAML files, cached previews and the run-history SQLite
database live on disk (see `crucible_workspace.paths`), and exposes small
facades (`WorkflowStore`, `PreviewCache`, `RuntimeDataStorage`) over that
storage for `crucible_server` to use.
"""

from crucible_workspace.models import WorkflowInfo
from crucible_workspace.store import WorkflowStore
from crucible_workspace.cache import PreviewCache, CachedPreview
from crucible_workspace.runtime import RuntimeDataStorage
__all__ = [
    "WorkflowInfo",
    "WorkflowStore",
    "PreviewCache",
    "CachedPreview",
    "RuntimeDataStorage",
]

__version__ = "v0.1.0"

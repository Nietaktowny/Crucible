"""
Domain exceptions and runtime guards used by the workflow engine.

Guards (`MissingColumnsGuard`, `MissingFileGuard`, `ColumnsTypeGuard`,
`LazyFrameInstanceGuard`) are checked by `WorkflowExecutor` before each
step runs and raise the exceptions defined here when a precondition isn't
met, producing clearer failures than letting Polars raise its own errors
deep inside a step's `execute()`.
"""

from crucible.errors._errors import (
    ColumnNotFoundError,
    ColumnTypeMismatchError,
    InvalidWorkflowPlan
)

from crucible.errors.guards import (
    ColumnsTypeGuard,
    MissingColumnsGuard,
    MissingFileGuard,
    LazyFrameInstanceGuard
)

__all__ = [
    "ColumnNotFoundError",
    "ColumnTypeMismatchError",
    "InvalidWorkflowPlan",
    "ColumnsTypeGuard",
    "MissingColumnsGuard",
    "MissingFileGuard",
    "LazyFrameInstanceGuard"
]
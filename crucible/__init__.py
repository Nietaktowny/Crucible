"""
Crucible: a local-first workflow engine for data transformation and reporting.

Workflows are declarative YAML files describing an ordered list of steps
(read/transform/write). This top-level package exposes the small,
programmatic surface most callers need: `run_workflow`/`WorkflowRunner` to
execute a workflow file, `WorkflowRunResult` for its outcome, and
`get_steps_schema` to introspect every registered step's configuration
schema. See `crucible.workflow` for the loader/compiler/executor pipeline
and `crucible.steps` for the built-in step implementations.
"""

from crucible.runner import WorkflowRunner, WorkflowRunResult, run_workflow, get_steps_schema

__all__ = [
    "WorkflowRunner",
    "WorkflowRunResult",
    "run_workflow",
    "get_steps_schema"
]
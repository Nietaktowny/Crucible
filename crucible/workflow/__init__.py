"""
The workflow pipeline: `WorkflowLoader` parses a YAML file into a
`Workflow`, `WorkflowPreprocessor` validates and enriches it,
`WorkflowCompiler` resolves each step config into a concrete `Step`
instance, `WorkflowOptimizer` applies structural optimizations to the
compiled plan, and `WorkflowExecutor` runs it. `StepsRegistry` maps step
`key`s to their implementation classes, used by the compiler.
"""

from crucible.workflow.executor import WorkflowExecutor
from crucible.workflow.compiler import WorkflowCompiler
from crucible.workflow.loader import WorkflowLoader
from crucible.workflow.optimizer import WorkflowOptimizer
from crucible.workflow.preprocessor import WorkflowPreprocessor
from crucible.workflow.registry import StepsRegistry

__all__ = [
    "WorkflowExecutor",
    "WorkflowCompiler",
    "WorkflowLoader",
    "WorkflowOptimizer",
    "WorkflowPreprocessor",
    "StepsRegistry"
]
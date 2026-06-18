
from typing import Any
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from crucible.models import (
    WorkflowRunResult,
    WorkflowRunConfig
)
from crucible.workflow import (
    WorkflowExecutor,
    WorkflowCompiler,
    WorkflowLoader,
    WorkflowOptimizer,
    WorkflowPreprocessor,
    StepsRegistry
)

class WorkflowRunner:
    """
    Public programmatic interface for running Crucible workflows.

    This class is intended for:
    - crucible-server
    - future desktop GUI
    - tests
    - external Python users

    CLI should only be a thin wrapper over this.
    """

    def __init__(
        self,
        loader: WorkflowLoader | None = None,
        preprocessor: WorkflowPreprocessor | None = None,
        optimizer: WorkflowOptimizer | None = None,
        compiler: WorkflowCompiler | None = None,
        executor: WorkflowExecutor | None = None,
    ) -> None:
        self.loader = loader or WorkflowLoader()
        self.preprocessor = preprocessor or WorkflowPreprocessor()
        self.optimizer = optimizer or WorkflowOptimizer()
        self.compiler = compiler or WorkflowCompiler()
        self.executor = executor or WorkflowExecutor()

    def run(self, workflow_path: Path, *,
            print_plan: bool = False,
            inspect: bool = False,
            preview_limit: int = 500
        ) -> WorkflowRunResult:
        workflow_path = Path(workflow_path)
        config = WorkflowRunConfig(
            inspect=inspect,
            preview_limit=preview_limit
        )

        workflow = self.loader.load(workflow_path)
        workflow = self.preprocessor.preprocess(workflow, config=config)
        workflow = self.compiler.compile(workflow, config=config)
        workflow = self.optimizer.optimize(workflow, config=config)

        if print_plan:
            self.compiler.print_execution_plan(workflow)

        return self.executor.run(workflow)


def run_workflow(
    workflow_path: Path,
    *,
    print_plan: bool = False,
    inspect: bool = False,
    preview_limit: int = 500
) -> WorkflowRunResult:
    return WorkflowRunner().run(
        workflow_path=workflow_path,
        inspect=inspect,
        print_plan=print_plan,
        preview_limit=preview_limit
    )
    
def get_steps_schema() -> list[dict[str, Any]]:
    registry = StepsRegistry()
    return registry.list_step_keys()
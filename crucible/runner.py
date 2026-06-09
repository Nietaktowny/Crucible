from dataclasses import dataclass
from pathlib import Path

from crucible.workflow import WorkflowExecutor
from crucible.workflow.compiler import WorkflowCompiler
from crucible.workflow.loader import WorkflowLoader
from crucible.workflow.optimizer import WorkflowOptimizer
from crucible.workflow.preprocessor import WorkflowPreprocessor


@dataclass(frozen=True)
class WorkflowRunResult:
    workflow_path: Path
    success: bool = True


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

    def run(self, workflow_path: Path, *, print_plan: bool = False) -> WorkflowRunResult:
        workflow_path = Path(workflow_path)

        workflow = self.loader.load(workflow_path)
        workflow = self.preprocessor.preprocess(workflow)
        workflow = self.optimizer.optimize(workflow)

        execution_plan = self.compiler.compile(workflow)

        if print_plan:
            self.compiler.print_execution_plan(execution_plan)

        self.executor.run(execution_plan)

        return WorkflowRunResult(
            workflow_path=workflow_path,
            success=True,
        )


def run_workflow(
    workflow_path: Path,
    *,
    print_plan: bool = False,
) -> WorkflowRunResult:
    return WorkflowRunner().run(
        workflow_path=workflow_path,
        print_plan=print_plan,
    )
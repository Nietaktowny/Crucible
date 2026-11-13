"""In-memory evaluation using the same compiler, guards and executor as runs."""

from collections.abc import Callable

from crucible.models import FrameContext, StepConfig, StepExecutionContext, Workflow
from crucible.workflow.compiler import WorkflowCompiler
from crucible.workflow.executor import WorkflowExecutor


class EvaluationError(ValueError):
    """A draft or dependency failed at a configured step."""

    def __init__(self, message: str, step: StepConfig, workflow_name: str):
        self.step_id = step.step_id
        self.step_name = step.name or step.key
        self.workflow_name = workflow_name
        super().__init__(message)


class WorkflowEvaluator:
    """Evaluate a prefix without saving files, running writers or recording runs."""

    def __init__(self, resolve_workflow: Callable[[str], Workflow]):
        self.resolve_workflow = resolve_workflow

    def context(self, stack: tuple[str, ...], validate_data: bool = False) -> StepExecutionContext:
        def resolve(name: str) -> FrameContext:
            if name in stack:
                raise ValueError(f"Workflow dependency cycle: {' -> '.join((*stack, name))}")
            workflow = self.resolve_workflow(name)
            frame, _ = self.evaluate(workflow, stack=(*stack, name), validate_data=validate_data)
            return frame

        return StepExecutionContext(workflow_resolver=resolve)

    def evaluate(
        self,
        workflow: Workflow,
        step_id: str | None = None,
        *,
        before: bool = False,
        stack: tuple[str, ...] | None = None,
        validate_data: bool = False,
    ) -> tuple[FrameContext, dict[str, str]]:
        """Return the selected output and its input schema.

        Data is kept lazy during normal previews. When diagnosing a deferred
        collection failure, `validate_data` locates the original failing step.
        """
        steps = workflow.steps
        if step_id is not None:
            index = next((i for i, step in enumerate(steps) if step.step_id == step_id), None)
            if index is None:
                raise ValueError(f"Step not found: {step_id}")
            steps = steps[:index + (0 if before else 1)]
        active = workflow.model_copy(update={"steps": [
            step for step in steps if step.key not in {"write_csv", "write_excel", "__inspect_frame"}
        ]})
        if not active.steps:
            raise ValueError("Add a source step to preview data")

        compiler = WorkflowCompiler()
        # Validate each configuration separately so errors keep the editor's IDs.
        for step in active.steps:
            try:
                compiler.compile(workflow.model_copy(update={"steps": [step]}))
            except Exception as exc:
                raise EvaluationError(str(exc), step, workflow.name) from exc
        plan = compiler.compile(active)
        frames: list[FrameContext] = []
        input_schema: dict[str, str] = {}

        def capture(_step: StepConfig, input_frame: FrameContext | None, output_frame: FrameContext) -> None:
            nonlocal input_schema
            if validate_data:
                output_frame.df.collect()
            frames.append(output_frame)
            input_schema = input_frame.schema if input_frame is not None else {}

        result = WorkflowExecutor().run(
            plan,
            context=self.context(stack or (workflow.name,), validate_data=validate_data),
            preview_mode=True,
            on_frame=capture,
        )
        if result.error is not None:
            error = result.error.error
            if isinstance(error, EvaluationError):
                raise error
            step = next(
                (item.config for item in plan.steps_execution_plan if item.config.step_id == result.error.step_id),
                active.steps[-1],
            )
            raise EvaluationError(str(error), step, workflow.name) from error
        if step_id is not None:
            target = next(step for step in workflow.steps if step.step_id == step_id)
            if not before and target.key in {"write_csv", "write_excel", "__inspect_frame"}:
                input_schema = frames[-1].schema
        return frames[-1], input_schema

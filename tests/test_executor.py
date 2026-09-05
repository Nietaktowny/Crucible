import polars as pl
from pydantic import BaseModel

from crucible.models import (
    FrameContext,
    Step,
    StepConfig,
    StepExecutionContext,
    StepExecutionPlan,
    StepStatus,
    Workflow,
    WorkflowExecutionPlan,
    WorkflowStatus,
)
from crucible.workflow.executor import WorkflowExecutor


class DummyConfig(BaseModel):
    value: str | None = None


class RecordingStep(Step):
    key = "recording"
    name = "Recording Step"
    description = "Records execution order"
    config_model = DummyConfig

    def __init__(self, config: StepConfig, calls: list[str]) -> None:
        super().__init__(config)
        self.calls = calls

    def execute(
        self,
        data: FrameContext | None,
        context: StepExecutionContext = None,
    ) -> FrameContext | None:
        self.calls.append(self.config.value)
        return data


class DataProducingStep(Step):
    key = "producer"
    name = "Producer"
    description = "Produces data"
    config_model = None

    def execute(
        self,
        data: FrameContext | None,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        preview = pl.DataFrame({"value": [1, 2, 3]})

        return FrameContext(
            df=preview.lazy(),
            preview=preview,
            row_count=3,
        )


class DataConsumingStep(Step):
    key = "consumer"
    name = "Consumer"
    description = "Consumes data"
    config_model = None

    def __init__(self, config: StepConfig) -> None:
        super().__init__(config)
        self.received_data: FrameContext | None = None

    def execute(
        self,
        data: FrameContext | None,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        self.received_data = data
        return data


class ContextStep(Step):
    key = "context"
    name = "Context Step"
    description = "Validates context"
    config_model = None

    def __init__(self, config: StepConfig) -> None:
        super().__init__(config)
        self.received_context: StepExecutionContext | None = None

    def execute(
        self,
        data: FrameContext | None,
        context: StepExecutionContext = None,
    ) -> FrameContext | None:
        self.received_context = context
        return data


class FailingStep(Step):
    key = "failing"
    name = "Failing Step"
    description = "Always fails"
    config_model = None

    def execute(
        self,
        data: FrameContext | None,
        context: StepExecutionContext = None,
    ) -> FrameContext:
        raise RuntimeError("Test failure")


class NeverExecutedStep(Step):
    key = "never"
    name = "Never Executed"
    description = "Should never run"
    config_model = None

    def __init__(self, config: StepConfig) -> None:
        super().__init__(config)
        self.executed = False

    def execute(
        self,
        data: FrameContext | None,
        context: StepExecutionContext = None,
    ) -> FrameContext | None:
        self.executed = True
        return data


def make_execution_plan(*steps: Step) -> WorkflowExecutionPlan:
    return WorkflowExecutionPlan(
        workflow=Workflow(
            name="test_workflow",
            steps=[],
        ),
        steps_execution_plan=[
            StepExecutionPlan(
                step=step,
                config=StepConfig(key=step.key),
            )
            for step in steps
        ],
    )


def test_run_empty_execution_plan() -> None:
    executor = WorkflowExecutor()

    plan = WorkflowExecutionPlan(
        workflow=Workflow(
            name="empty",
            steps=[],
        ),
        steps_execution_plan=[],
    )

    result = executor.run(plan)

    assert plan.steps_execution_plan == []

    assert result.status == WorkflowStatus.RUNNING
    assert result.success is False
    assert result.preview is None
    assert result.row_count is None
    assert result.error is None

    assert result.statistics.total_steps == 0
    assert result.statistics.system_steps == 0
    assert result.statistics.started_at is not None
    assert result.statistics.ended_at is not None
    assert result.statistics.total_time >= 0


def test_run_executes_all_steps_in_order() -> None:
    executor = WorkflowExecutor()

    calls: list[str] = []

    step_1 = RecordingStep(
        StepConfig(key="recording", parameters={"value": "step_1"}),
        calls,
    )
    step_2 = RecordingStep(
        StepConfig(key="recording", parameters={"value": "step_2"}),
        calls,
    )
    step_3 = RecordingStep(
        StepConfig(key="recording", parameters={"value": "step_3"}),
        calls,
    )

    plan = make_execution_plan(step_1, step_2, step_3)

    result = executor.run(plan)

    assert calls == ["step_1", "step_2", "step_3"]

    assert all(
        step_plan.status == StepStatus.SUCCESS
        for step_plan in plan.steps_execution_plan
    )

    assert result.status == WorkflowStatus.SUCCESS
    assert result.success is True
    assert result.error is None
    assert result.preview is None
    assert result.row_count is None
    assert result.statistics.total_steps == 3


def test_run_marks_successful_steps_as_success() -> None:
    executor = WorkflowExecutor()

    step = RecordingStep(
        StepConfig(key="recording", parameters={"value": "test"}),
        [],
    )

    plan = make_execution_plan(step)

    result = executor.run(plan)

    assert plan.steps_execution_plan[0].status == StepStatus.SUCCESS

    assert result.status == WorkflowStatus.SUCCESS
    assert result.success is True
    assert result.error is None


def test_run_passes_data_between_steps() -> None:
    executor = WorkflowExecutor()

    producer = DataProducingStep(StepConfig(key="producer"))
    consumer = DataConsumingStep(StepConfig(key="consumer"))

    plan = make_execution_plan(producer, consumer)

    result = executor.run(plan)

    assert consumer.received_data is not None
    assert isinstance(consumer.received_data, FrameContext)

    collected = consumer.received_data.collect()

    assert collected.shape == (3, 1)
    assert collected["value"].to_list() == [1, 2, 3]

    assert result.status == WorkflowStatus.SUCCESS
    assert result.success is True
    assert result.error is None

    assert result.preview is not None
    assert len(result.preview) == 3
    assert [row["value"] for row in result.preview] == [1, 2, 3]
    assert result.row_count == 3


def test_run_passes_same_context_instance_between_steps() -> None:
    executor = WorkflowExecutor()

    step_1 = ContextStep(StepConfig(key="context"))
    step_2 = ContextStep(StepConfig(key="context"))

    plan = make_execution_plan(step_1, step_2)

    result = executor.run(plan)

    assert step_1.received_context is not None
    assert step_2.received_context is not None
    assert step_1.received_context is step_2.received_context

    assert result.status == WorkflowStatus.SUCCESS
    assert result.success is True
    assert result.error is None


def test_run_initial_data_is_none() -> None:
    received_values: list[FrameContext | None] = []

    class CaptureInputStep(Step):
        key = "capture"
        name = "Capture"
        description = "Capture initial input"
        config_model = None

        def execute(
            self,
            data: FrameContext | None,
            context: StepExecutionContext = None,
        ) -> FrameContext | None:
            received_values.append(data)
            return data

    executor = WorkflowExecutor()

    step = CaptureInputStep(StepConfig(key="capture"))
    plan = make_execution_plan(step)

    result = executor.run(plan)

    assert received_values == [None]

    assert result.status == WorkflowStatus.SUCCESS
    assert result.success is True
    assert result.preview is None
    assert result.row_count is None
    assert result.error is None


def test_run_returns_successful_workflow_result() -> None:
    executor = WorkflowExecutor()

    step = DataProducingStep(StepConfig(key="producer"))
    plan = make_execution_plan(step)

    result = executor.run(plan)

    assert result.status == WorkflowStatus.SUCCESS
    assert result.success is True
    assert result.error is None

    assert result.preview is not None
    assert [row["value"] for row in result.preview] == [1, 2, 3]
    assert result.row_count == 3

    assert result.statistics.total_steps == 1
    assert result.statistics.system_steps == 0
    assert result.statistics.started_at is not None
    assert result.statistics.ended_at is not None
    assert result.statistics.total_time >= 0


def test_run_returns_failed_workflow_result_when_step_fails() -> None:
    executor = WorkflowExecutor()

    failing_step = FailingStep(StepConfig(key="failing"))
    never_step = NeverExecutedStep(StepConfig(key="never"))

    plan = make_execution_plan(failing_step, never_step)

    result = executor.run(plan)

    assert result.status == WorkflowStatus.FAILED
    assert result.success is False
    assert isinstance(result.error.error, RuntimeError)
    assert str(result.error.error) == "Test failure"

    assert plan.steps_execution_plan[0].status == StepStatus.FAILED
    assert plan.steps_execution_plan[1].status == StepStatus.WAITING

    assert never_step.executed is False

    assert result.preview is None
    assert result.row_count is None

    assert result.statistics.total_steps == 2
    assert result.statistics.system_steps == 0
    assert result.statistics.started_at is not None
    assert result.statistics.ended_at is not None
    assert result.statistics.total_time >= 0


def test_run_counts_system_steps() -> None:
    executor = WorkflowExecutor()

    class SystemStep(RecordingStep):
        key = "__inspect_preview"
        name = "Inspect Preview"
        description = "System inspect step"

    calls: list[str] = []

    normal_step = RecordingStep(
        StepConfig(key="recording", parameters={"value": "normal"}),
        calls,
    )

    system_step = SystemStep(
        StepConfig(key="__inspect_preview", parameters={"value": "system"}),
        calls,
    )

    plan = make_execution_plan(normal_step, system_step)

    result = executor.run(plan)

    assert result.status == WorkflowStatus.SUCCESS
    assert result.statistics.total_steps == 2
    assert result.statistics.system_steps == 1


def test_run_logs_step_execution(caplog) -> None:
    executor = WorkflowExecutor()

    step = RecordingStep(
        StepConfig(key="recording", parameters={"value": "test"}),
        [],
    )

    plan = make_execution_plan(step)

    with caplog.at_level("INFO"):
        result = executor.run(plan)

    assert "Executing step: Recording Step" in caplog.text

    assert result.status == WorkflowStatus.SUCCESS
    assert result.success is True
    assert result.error is None
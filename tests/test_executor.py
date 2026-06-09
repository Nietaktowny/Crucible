import pytest
import polars as pl
from pydantic import BaseModel

from crucible.models import (
    Step,
    StepConfig,
    StepExecutionContext,
    StepExecutionPlan,
    StepStatus,
    Workflow,
    WorkflowExecutionPlan,
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
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        self.calls.append(self.config.value)
        return data


class DataProducingStep(Step):
    key = "producer"
    name = "Producer"
    description = "Produces data"
    config_model = None

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        return pl.DataFrame(
            {"value": [1, 2, 3]}
        ).lazy()


class DataConsumingStep(Step):
    key = "consumer"
    name = "Consumer"
    description = "Consumes data"
    config_model = None

    def __init__(self, config: StepConfig) -> None:
        super().__init__(config)
        self.received_data = None

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        self.received_data = data
        return data


class ContextStep(Step):
    key = "context"
    name = "Context Step"
    description = "Validates context"
    config_model = None

    def __init__(self, config: StepConfig) -> None:
        super().__init__(config)
        self.received_context = None

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        self.received_context = context
        return data


class FailingStep(Step):
    key = "failing"
    name = "Failing Step"
    description = "Always fails"
    config_model = None

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
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
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        self.executed = True
        return data


def make_execution_plan(
    *steps: Step,
) -> WorkflowExecutionPlan:
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

    executor.run(plan)

    assert plan.steps_execution_plan == []


def test_run_executes_all_steps_in_order() -> None:
    executor = WorkflowExecutor()

    calls: list[str] = []

    step_1 = RecordingStep(
        StepConfig(
            key="recording",
            parameters={"value": "step_1"},
        ),
        calls,
    )

    step_2 = RecordingStep(
        StepConfig(
            key="recording",
            parameters={"value": "step_2"},
        ),
        calls,
    )

    step_3 = RecordingStep(
        StepConfig(
            key="recording",
            parameters={"value": "step_3"},
        ),
        calls,
    )

    plan = make_execution_plan(
        step_1,
        step_2,
        step_3,
    )

    executor.run(plan)

    assert calls == [
        "step_1",
        "step_2",
        "step_3",
    ]

    assert all(
        step_plan.status == StepStatus.SUCCESS
        for step_plan in plan.steps_execution_plan
    )


def test_run_marks_successful_steps_as_success() -> None:
    executor = WorkflowExecutor()

    step = RecordingStep(
        StepConfig(
            key="recording",
            parameters={"value": "test"},
        ),
        [],
    )

    plan = make_execution_plan(step)

    executor.run(plan)

    assert plan.steps_execution_plan[0].status == StepStatus.SUCCESS


def test_run_passes_data_between_steps() -> None:
    executor = WorkflowExecutor()

    producer = DataProducingStep(
        StepConfig(key="producer")
    )

    consumer = DataConsumingStep(
        StepConfig(key="consumer")
    )

    plan = make_execution_plan(
        producer,
        consumer,
    )

    executor.run(plan)

    assert consumer.received_data is not None

    collected = consumer.received_data.collect()

    assert collected.shape == (3, 1)
    assert collected["value"].to_list() == [1, 2, 3]


def test_run_passes_same_context_instance_between_steps() -> None:
    executor = WorkflowExecutor()

    step_1 = ContextStep(
        StepConfig(key="context")
    )

    step_2 = ContextStep(
        StepConfig(key="context")
    )

    plan = make_execution_plan(
        step_1,
        step_2,
    )

    executor.run(plan)

    assert step_1.received_context is not None
    assert step_2.received_context is not None
    assert step_1.received_context is step_2.received_context


def test_run_initial_data_is_none() -> None:
    received_values = []

    class CaptureInputStep(Step):
        key = "capture"
        name = "Capture"
        description = "Capture initial input"

        def execute(
            self,
            data: pl.LazyFrame,
            context: StepExecutionContext = None,
        ) -> pl.LazyFrame:
            received_values.append(data)
            return data

    executor = WorkflowExecutor()

    step = CaptureInputStep(
        StepConfig(key="capture")
    )

    plan = make_execution_plan(step)

    executor.run(plan)

    assert received_values == [None]

def test_run_logs_step_execution(caplog) -> None:
    executor = WorkflowExecutor()

    step = RecordingStep(
        StepConfig(
            key="recording",
            parameters={"value": "test"},
        ),
        [],
    )

    plan = make_execution_plan(step)

    with caplog.at_level("INFO"):
        executor.run(plan)

    assert "Executing step: Recording Step" in caplog.text
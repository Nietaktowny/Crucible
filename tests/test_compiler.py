import pytest
import polars as pl
from pydantic import BaseModel

from crucible.models import (
    MultiSourcesStepConfig,
    Step,
    StepConfig,
    StepExecutionPlan,
    StepExecutionContext,
    StepStatus,
    Workflow,
    WorkflowExecutionPlan,
)
from crucible.workflow.compiler import PlanBuilder, WorkflowCompiler


class DummyConfig(BaseModel):
    value: str | None = None


class DummyStep(Step):
    key = "dummy"
    name = "Dummy Step"
    description = "Dummy test step"
    config_model = DummyConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        return data


class SourceStep(Step):
    key = "source"
    name = "Source Step"
    description = "Source test step"
    config_model = DummyConfig

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        return data


class MultiStep(Step):
    key = "multi"
    name = "Multi Step"
    description = "Multi-source test step"
    config_model = None

    def execute(
        self,
        data: pl.LazyFrame,
        context: StepExecutionContext = None,
    ) -> pl.LazyFrame:
        return data


class FakeStepsRegistry:
    def get_step(self, key: str, step_config: StepConfig) -> Step:
        step_map = {
            "dummy": DummyStep,
            "source": SourceStep,
            "multi": MultiStep,
        }

        try:
            step_cls = step_map[key]
        except KeyError:
            raise KeyError(f"Unknown step key: {key}")

        return step_cls(step_config)


@pytest.fixture
def compiler() -> WorkflowCompiler:
    compiler = WorkflowCompiler()
    compiler.steps_registry = FakeStepsRegistry()
    return compiler


def make_plan_node(key: str = "dummy") -> StepExecutionPlan:
    config = StepConfig(key=key)
    step = DummyStep(config)

    return StepExecutionPlan(
        step=step,
        config=config,
    )


def test_plan_builder_add_node_returns_same_node() -> None:
    builder = PlanBuilder()
    node = make_plan_node()

    result = builder.add_node(node)

    assert result is node
    assert builder.nodes == [node]


def test_plan_builder_add_edge_registers_edge() -> None:
    builder = PlanBuilder()
    source = make_plan_node()
    target = make_plan_node()

    builder.add_node(source)
    builder.add_node(target)
    builder.add_edge(source, target)

    assert builder.edges == [(source, target)]


def test_plan_builder_predecessors_returns_direct_sources() -> None:
    builder = PlanBuilder()
    first = make_plan_node()
    second = make_plan_node()
    third = make_plan_node()

    builder.add_node(first)
    builder.add_node(second)
    builder.add_node(third)

    builder.add_edge(first, third)
    builder.add_edge(second, third)

    assert builder.predecessors(third) == [first, second]


def test_plan_builder_insert_between_replaces_single_edge_with_chain() -> None:
    builder = PlanBuilder()

    source = make_plan_node()
    target = make_plan_node()
    inserted_1 = make_plan_node()
    inserted_2 = make_plan_node()

    builder.add_node(source)
    builder.add_node(target)
    builder.add_edge(source, target)

    builder.insert_between(source, target, [inserted_1, inserted_2])

    assert (source, target) not in builder.edges
    assert builder.edges == [
        (source, inserted_1),
        (inserted_1, inserted_2),
        (inserted_2, target),
    ]
    assert inserted_1 in builder.nodes
    assert inserted_2 in builder.nodes


def test_plan_builder_insert_before_without_predecessors_adds_edge_to_target() -> None:
    builder = PlanBuilder()

    target = make_plan_node()
    inserted = make_plan_node()

    builder.add_node(target)

    builder.insert_before(target, inserted)

    assert inserted in builder.nodes
    assert builder.edges == [(inserted, target)]


def test_plan_builder_insert_before_with_predecessors_redirects_edges() -> None:
    builder = PlanBuilder()

    predecessor_1 = make_plan_node()
    predecessor_2 = make_plan_node()
    target = make_plan_node()
    inserted = make_plan_node()

    for node in [predecessor_1, predecessor_2, target]:
        builder.add_node(node)

    builder.add_edge(predecessor_1, target)
    builder.add_edge(predecessor_2, target)

    builder.insert_before(target, inserted)

    assert (predecessor_1, target) not in builder.edges
    assert (predecessor_2, target) not in builder.edges

    assert set(builder.edges) == {
        (predecessor_1, inserted),
        (predecessor_2, inserted),
        (inserted, target),
    }


def test_plan_builder_insert_chain_before_with_empty_list_does_nothing() -> None:
    builder = PlanBuilder()

    target = make_plan_node()
    builder.add_node(target)

    builder.insert_chain_before(target, [])

    assert builder.nodes == [target]
    assert builder.edges == []


def test_plan_builder_insert_chain_before_without_predecessors_adds_only_last_edge() -> None:
    builder = PlanBuilder()

    target = make_plan_node()
    inserted_1 = make_plan_node()
    inserted_2 = make_plan_node()

    builder.add_node(target)

    builder.insert_chain_before(target, [inserted_1, inserted_2])

    assert inserted_1 in builder.nodes
    assert inserted_2 in builder.nodes
    assert builder.edges == [(inserted_2, target)]


def test_plan_builder_insert_chain_before_with_predecessor_redirects_to_chain() -> None:
    builder = PlanBuilder()

    predecessor = make_plan_node()
    target = make_plan_node()
    inserted_1 = make_plan_node()
    inserted_2 = make_plan_node()

    builder.add_node(predecessor)
    builder.add_node(target)
    builder.add_edge(predecessor, target)

    builder.insert_chain_before(target, [inserted_1, inserted_2])

    assert builder.edges == [
        (predecessor, inserted_1),
        (inserted_1, inserted_2),
        (inserted_2, target),
    ]


def test_plan_builder_build_order_returns_topological_order() -> None:
    builder = PlanBuilder()

    first = make_plan_node()
    second = make_plan_node()
    third = make_plan_node()

    for node in [first, second, third]:
        builder.add_node(node)

    builder.add_edge(first, second)
    builder.add_edge(second, third)

    assert builder.build_order() == [first, second, third]


def test_compiler_build_step_plan_creates_step_execution_plan(compiler: WorkflowCompiler) -> None:
    config = StepConfig(
        key="dummy",
        parameters={"value": "abc"},
    )

    plan = compiler._build_step_plan(config)

    assert isinstance(plan, StepExecutionPlan)
    assert isinstance(plan.step, DummyStep)
    assert plan.config is config
    assert plan.status == StepStatus.WAITING
    assert plan.step.config.value == "abc"


def test_compiler_compile_empty_workflow_returns_empty_execution_plan(
    compiler: WorkflowCompiler,
) -> None:
    workflow = Workflow(name="empty", steps=[])

    plan = compiler.compile(workflow)

    assert isinstance(plan, WorkflowExecutionPlan)
    assert plan.workflow is workflow
    assert plan.steps_execution_plan == []


def test_compiler_compile_single_step_workflow(
    compiler: WorkflowCompiler,
) -> None:
    workflow = Workflow(
        name="single",
        steps=[
            StepConfig(key="dummy", parameters={"value": "one"}),
        ],
    )

    plan = compiler.compile(workflow)

    assert [step_plan.step.key for step_plan in plan.steps_execution_plan] == [
        "dummy",
    ]
    assert plan.steps_execution_plan[0].step.config.value == "one"


def test_compiler_compile_multiple_steps_preserves_linear_order(
    compiler: WorkflowCompiler,
) -> None:
    workflow = Workflow(
        name="linear",
        steps=[
            StepConfig(key="dummy", parameters={"value": "first"}),
            StepConfig(key="dummy", parameters={"value": "second"}),
            StepConfig(key="dummy", parameters={"value": "third"}),
        ],
    )

    plan = compiler.compile(workflow)

    assert [step_plan.step.config.value for step_plan in plan.steps_execution_plan] == [
        "first",
        "second",
        "third",
    ]


def test_compiler_expands_multisource_step_before_target(
    compiler: WorkflowCompiler,
) -> None:
    workflow = Workflow(
        name="multi_source_workflow",
        steps=[
            MultiSourcesStepConfig(
                key="multi",
                sources=[
                    StepConfig(key="source", parameters={"value": "source_1"}),
                    StepConfig(key="source", parameters={"value": "source_2"}),
                ],
            ),
        ],
    )

    plan = compiler.compile(workflow)

    assert [step_plan.step.key for step_plan in plan.steps_execution_plan] == [
        "source",
        "source",
        "multi",
    ]

    assert plan.steps_execution_plan[0].step.config.value == "source_1"
    assert plan.steps_execution_plan[1].step.config.value == "source_2"


def test_compiler_expands_multisource_step_inside_linear_workflow(
    compiler: WorkflowCompiler,
) -> None:
    workflow = Workflow(
        name="linear_with_multi",
        steps=[
            StepConfig(key="dummy", parameters={"value": "before"}),
            MultiSourcesStepConfig(
                key="multi",
                sources=[
                    StepConfig(key="source", parameters={"value": "source_1"}),
                    StepConfig(key="source", parameters={"value": "source_2"}),
                ],
            ),
            StepConfig(key="dummy", parameters={"value": "after"}),
        ],
    )

    plan = compiler.compile(workflow)

    assert [step_plan.step.key for step_plan in plan.steps_execution_plan] == [
        "dummy",
        "source",
        "source",
        "multi",
        "dummy",
    ]

    assert [getattr(step_plan.step.config, "value", None) for step_plan in plan.steps_execution_plan] == [
        "before",
        "source_1",
        "source_2",
        None,
        "after",
    ]


def test_compiler_expands_multisource_step_with_no_sources(
    compiler: WorkflowCompiler,
) -> None:
    workflow = Workflow(
        name="multi_without_sources",
        steps=[
            StepConfig(key="dummy", parameters={"value": "before"}),
            MultiSourcesStepConfig(
                key="multi",
                sources=[],
            ),
            StepConfig(key="dummy", parameters={"value": "after"}),
        ],
    )

    plan = compiler.compile(workflow)

    assert [step_plan.step.key for step_plan in plan.steps_execution_plan] == [
        "dummy",
        "multi",
        "dummy",
    ]


def test_compiler_compile_raises_for_unknown_step_key(
    compiler: WorkflowCompiler,
) -> None:
    workflow = Workflow(
        name="unknown",
        steps=[
            StepConfig(key="unknown"),
        ],
    )

    with pytest.raises(KeyError):
        compiler.compile(workflow)


def test_format_execution_plan_contains_workflow_name_and_steps(
    compiler: WorkflowCompiler,
) -> None:
    workflow = Workflow(
        name="format_test",
        steps=[
            StepConfig(key="dummy", parameters={"value": "abc"}),
        ],
    )

    plan = compiler.compile(workflow)
    output = compiler._format_execution_plan(plan)

    assert "Workflow: format_test" in output
    assert "01 dummy" in output
    assert "DummyStep" in output
    assert "value = abc" in output


def test_format_execution_plan_contains_sources_for_multisource_step(
    compiler: WorkflowCompiler,
) -> None:
    workflow = Workflow(
        name="format_sources_test",
        steps=[
            MultiSourcesStepConfig(
                key="multi",
                sources=[
                    StepConfig(key="source", parameters={"value": "source_1"}),
                ],
            ),
        ],
    )

    plan = compiler.compile(workflow)
    output = compiler._format_execution_plan(plan)

    assert "Workflow: format_sources_test" in output
    assert "sources" in output
    assert "source" in output
    assert "source_1" in output


def test_print_execution_plan_does_not_raise_when_debug_disabled(
    compiler: WorkflowCompiler,
) -> None:
    workflow = Workflow(
        name="print_test",
        steps=[
            StepConfig(key="dummy"),
        ],
    )

    plan = compiler.compile(workflow)

    compiler.print_execution_plan(plan)
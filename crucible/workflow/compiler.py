import logging

from crucible.models import (
    Workflow,
    StepExecutionPlan,
    WorkflowExecutionPlan,
    StepConfig,
    MultiSourcesStepConfig,
    WorkflowRunConfig
)
from crucible.models._workflow import StepConfig
from crucible.workflow.registry import StepsRegistry
from graphlib import TopologicalSorter
from itertools import pairwise

from rich.tree import Tree
from rich.console import Console

logger = logging.getLogger(__name__)
class PlanBuilder:
    def __init__(self) -> None:
        self.nodes: list[StepExecutionPlan] = []
        self.edges: list[tuple[StepExecutionPlan, StepExecutionPlan]] = []

    def add_node(self, node: StepExecutionPlan) -> StepExecutionPlan:
        self.nodes.append(node)
        return node

    def predecessors(self, node: StepExecutionPlan) -> list[StepExecutionPlan]:
        return [source for source, target in self.edges if target == node]

    def add_edge(self, source: StepExecutionPlan, target: StepExecutionPlan) -> None:
        self.edges.append((source, target))

    def insert_between(
        self,
        source: StepExecutionPlan,
        target: StepExecutionPlan,
        inserted: list[StepExecutionPlan],
    ) -> None:
        self.edges.remove((source, target))

        previous = source
        for node in inserted:
            self.add_node(node)
            self.add_edge(previous, node)
            previous = node

        self.add_edge(previous, target)

    def insert_before(
        self,
        target: StepExecutionPlan,
        inserted: StepExecutionPlan,
    ) -> None:
        predecessors = self.predecessors(target)

        if not predecessors:
            self.add_node(inserted)
            self.add_edge(inserted, target)
            return

        for predecessor in predecessors:
            self.edges.remove((predecessor, target))
            self.add_edge(predecessor, inserted)

        self.add_node(inserted)
        self.add_edge(inserted, target)
        
    def insert_chain_before(
        self,
        target: StepExecutionPlan,
        inserted: list[StepExecutionPlan],
    ) -> None:
        if not inserted:
            return

        predecessors = self.predecessors(target)

        for node in inserted:
            self.add_node(node)

        if not predecessors:
            self.add_edge(inserted[-1], target)
            return

        for predecessor in predecessors:
            self.edges.remove((predecessor, target))
            self.add_edge(predecessor, inserted[0])

        for source, target_node in pairwise(inserted):
            self.add_edge(source, target_node)

        self.add_edge(inserted[-1], target)

    def build_order(self) -> list[StepExecutionPlan]:
        sorter = TopologicalSorter()

        for node in self.nodes:
            sorter.add(node)

        for source, target in self.edges:
            sorter.add(target, source)

        return list(sorter.static_order())
class WorkflowCompiler:
    """
    Compiler and StepsRegistry should be:
    StepsRegistry -> knows of only single step it should create
    WorkflowCompiler -> knows of relations between steps
    """
    def __init__(self) -> None:
        self.steps_registry = StepsRegistry()

    def _build_step_plan(self, step_config: StepConfig) -> StepExecutionPlan:
        step = self.steps_registry.get_step(
            step_config.key,
            step_config=step_config,
        )

        return StepExecutionPlan(
            step=step,
            config=step_config,
        )

    def _expand_system_steps(self, builder: PlanBuilder) -> None:
        for node in list(builder.nodes):
            if isinstance(node.config, MultiSourcesStepConfig):
                source_nodes = [
                    self._build_step_plan(source_config)
                    for source_config in node.config.sources
                ]

                builder.insert_chain_before(node, source_nodes)

    def compile(self, workflow: Workflow, *, config: WorkflowRunConfig | None = None) -> WorkflowExecutionPlan:
        builder = PlanBuilder()

        nodes = [
            self._build_step_plan(step_config)
            for step_config in workflow.steps
        ]

        for node in nodes:
            builder.add_node(node)

        for source, target in pairwise(nodes):
            builder.add_edge(source, target)

        self._expand_system_steps(builder)

        return WorkflowExecutionPlan(
            workflow=workflow,
            steps_execution_plan=builder.build_order(),
        )

    def _format_execution_plan(self, plan: WorkflowExecutionPlan) -> str:
        console = Console(record=True, width=140)

        tree = Tree(f"[bold cyan]Workflow[/bold cyan]: {plan.workflow.name}")

        for index, step_plan in enumerate(plan.steps_execution_plan, start=1):
            step = step_plan.step

            node = tree.add(
                f"[green]{index:02d}[/green] "
                f"[yellow]{step.key}[/yellow] "
                f"({step.__class__.__name__})"
            )

            if step_plan.config.parameters:
                for key, value in step_plan.config.parameters.items():
                    node.add(f"{key} = {value}")

            sources = getattr(step_plan.config, "sources", None)

            if not sources and getattr(step_plan.config, "model_extra", None):
                sources = step_plan.config.model_extra.get("sources")

            if sources:
                sources_node = node.add("[magenta]sources[/magenta]")

                for source in sources:
                    if isinstance(source, dict):
                        sources_node.add(
                            f"{source.get('key')} {source.get('parameters', {})}"
                        )
                    else:
                        sources_node.add(
                            f"{source.key} {source.parameters}"
                        )

        console.print(tree)
        return console.export_text(styles=False)

    def print_execution_plan(self, plan: WorkflowExecutionPlan) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Compiled execution plan:")
            self._format_execution_plan(plan)
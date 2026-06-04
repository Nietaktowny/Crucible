from typing import Literal
from dataclasses import dataclass
import logging

from crucible.models import Workflow, StepConfig, IOConfig, StepStatus, StepExecutionPlan, WorkflowExecutionPlan, StepProtocol
from crucible.workflow.registry import StepsRegistry
from crucible.io import IOManagerProtocol, CsvIOManager


logger = logging.getLogger(__name__)

class WorkflowExecutor:
    def __init__(self) -> None:
        self.steps_registry = StepsRegistry()

    def get_io_manager(self, io_config: IOConfig) -> IOManagerProtocol:
        if io_config.type == ".csv":
            return CsvIOManager(io_config)
        else:
            raise ValueError(f"Unsupported IO type: {io_config.type}")
        
    def build_io_step(self, step_config: StepConfig, io_config: IOConfig) -> StepProtocol:
        io_manager = self.get_io_manager(io_config)
        return self.steps_registry.get_step(step_config.key, step_config=step_config, io_manager=io_manager)

    def add_io_steps(self, workflow: Workflow) -> Workflow:
        if workflow.input:
            read_step_config = StepConfig(
                key="read_data",
                parameters={}
            )
            workflow.steps.insert(0, read_step_config)
            
        if workflow.output:
            write_step_config = StepConfig(
                key="write_data",
                parameters={}
            )
            workflow.steps.append(write_step_config)
        return workflow

    def build(self, workflow: Workflow) -> WorkflowExecutionPlan:
        steps_execution_plan = []
        workflow = self.add_io_steps(workflow)
        for step_config in workflow.steps:
            if step_config.key in ["read_data", "write_data"]:
                step = self.build_io_step(step_config, workflow.input if step_config.key == "read_data" else workflow.output)
            else:
                step = self.steps_registry.get_step(step_config.key, step_config=step_config)
            if not step:
                raise ValueError(f"Step with key {step_config.key} not found in registry")
            
            step_execution_plan = StepExecutionPlan(
                step=step,
                config=step_config
            )
            steps_execution_plan.append(step_execution_plan)
            
        workflow_execution_plan = WorkflowExecutionPlan(
            workflow=workflow,
            steps_execution_plan=steps_execution_plan
        )
        logger.debug(f"Built workflow execution plan: {workflow_execution_plan}")
        return workflow_execution_plan
    
    def run(self, workflow_execution_plan: WorkflowExecutionPlan) -> None:
        data = None
        for step_execution_plan in workflow_execution_plan.steps_execution_plan:
            step = step_execution_plan.step
            config = step_execution_plan.config
            
            try:
                logger.debug(f"Executing step: {step.key} with config: {config}")
                data = step.execute(data)
                step_execution_plan.status = StepStatus.SUCCESS
            except Exception as e:
                step_execution_plan.status = StepStatus.FAILED
                logger.error(f"Step {step.key} failed with error: {e}")
                break

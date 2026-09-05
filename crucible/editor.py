from crucible.models import (
    Workflow,
    StepConfig
)

from crucible.workflow.registry import StepsRegistry

class WorkflowEditor():
    def __init__(self):
        self._registry = StepsRegistry()
        
    def add_step(self, workflow: Workflow, key: str) -> Workflow:
        step_config = self._registry.get_step()
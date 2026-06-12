from crucible.models import Workflow, StepConfig, WorkflowRunConfig
from crucible.errors import InvalidWorkflowPlan

class WorkflowPreprocessor:  
    def preprocess(self, workflow: Workflow, *, config: WorkflowRunConfig | None = None) -> Workflow:
        if len(workflow.steps) == 0:
            raise InvalidWorkflowPlan(f"Workflow must consist of at least one step. No steps found in workflow: '{workflow.name}'")
        
        config = config or WorkflowRunConfig()
        enriched_steps = workflow.steps.copy()
        
        if config.inspect is True:
            enriched_steps.append(StepConfig(
                key='__inspect_frame',
                parameters={
                    "preview_limit": config.preview_limit
                }
            ))
        return workflow.model_copy(update={"steps": enriched_steps})
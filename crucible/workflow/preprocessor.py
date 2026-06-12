from crucible.models import Workflow, StepConfig, WorkflowRunConfig

class WorkflowPreprocessor:  
    def preprocess(self, workflow: Workflow, *, config: WorkflowRunConfig | None = None) -> Workflow:
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
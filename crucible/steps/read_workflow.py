from pydantic import BaseModel, Field

from crucible.models import FrameContext, Step, StepExecutionContext


class ReadWorkflowConfig(BaseModel):
    """Reference the latest saved transformations of another workflow."""

    workflow_name: str = Field(min_length=1)
    context_store: bool = False
    context_key: str = "right"


class ReadWorkflowStep(Step):
    """Resolve a workflow using the runner's isolated, read-only evaluator."""

    key = "read_workflow"
    name = "Read Workflow"
    description = "Read the transformed output of another saved workflow."
    config_model = ReadWorkflowConfig

    def execute(
        self,
        data: FrameContext | None = None,
        context: StepExecutionContext | None = None,
    ) -> FrameContext:
        if context is None or context.workflow_resolver is None:
            raise ValueError("Read Workflow requires a workflow resolver")
        frame = context.workflow_resolver(self.config.workflow_name)
        if self.config.context_store:
            context.extra_inputs[self.config.context_key] = frame
        return frame if data is None else data

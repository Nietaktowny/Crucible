from crucible.models import Workflow, StepConfig, WorkflowRunConfig
from crucible.errors import InvalidWorkflowPlan

class WorkflowPreprocessor:
    """Validates and enriches a raw `Workflow` before compilation.

    Runs immediately after loading, before `WorkflowCompiler` resolves step
    configs into concrete step instances.
    """

    def preprocess(self, workflow: Workflow, *, config: WorkflowRunConfig | None = None) -> Workflow:
        """Validate a workflow and optionally append an inspection step.

        Rejects empty workflows outright. When `config.inspect` is enabled
        (the default), appends a system `__inspect_frame` step so the
        executor always ends with a step that captures a preview and row
        count for the run result — without every workflow author needing to
        add one manually.

        Args:
            workflow (Workflow): Raw workflow definition to preprocess.
            config (WorkflowRunConfig | None, optional): Run configuration; a
                default `WorkflowRunConfig()` is used when omitted. Defaults to None.

        Returns:
            Workflow: A new `Workflow` (via `model_copy`) with the inspection
                step appended when requested; the original `workflow` is left unmodified.

        Raises:
            InvalidWorkflowPlan: If `workflow.steps` is empty.
        """
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

import type { StepKey } from "@/features/workflow/stepRegistry";

export type WorkflowStep = {
  id: string;
  key: StepKey;
  name: string;
  description: string;
  parameters: Record<string, unknown>;
};

export type WorkflowSourceStep = Omit<WorkflowStep, "id"> & {
  id?: string;
  alias?: string;
  sources?: WorkflowSourceStep[];
};

export type MultiSourceWorkflowStep = WorkflowStep & {
  sources: WorkflowSourceStep[];
};

export type WorkflowEditorStep = WorkflowStep | MultiSourceWorkflowStep;

export type Workflow = {
  name: string;
  steps: WorkflowEditorStep[];
};

export function isMultiSourceStep(
  step: WorkflowEditorStep | WorkflowSourceStep,
): step is MultiSourceWorkflowStep {
  return Array.isArray((step as MultiSourceWorkflowStep).sources);
}
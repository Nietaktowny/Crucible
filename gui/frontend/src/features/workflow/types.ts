import type { StepKey } from "@/features/workflow/stepRegistry";

export type WorkflowStep = {
  id: string;
  key: StepKey;
  name: string;
  description: string;
  parameters: Record<string, unknown>;
};

export type Workflow = {
  name: string;
  steps: WorkflowStep[];
};
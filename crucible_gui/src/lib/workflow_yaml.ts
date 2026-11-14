import YAML from "yaml";

import type { WorkflowConfig } from "@/types/workflows";

export function serializeWorkflow(workflow: WorkflowConfig): string {
  // PyYAML resolves plain scalars using YAML 1.1 rules, including "=" as a
  // special tag. Quote strings so operators and literal values retain types.
  return YAML.stringify(workflow, { defaultStringType: "QUOTE_DOUBLE" });
}

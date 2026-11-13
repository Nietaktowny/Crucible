import type { StepConfig, WorkflowConfig } from "@/types/workflows";

export type EditorSnapshot = {
  workflow: WorkflowConfig;
  selectedId: string | null;
};
export type EditorState = {
  present: EditorSnapshot;
  past: EditorSnapshot[];
  future: EditorSnapshot[];
  saved: string;
};

export function initialEditor(workflow: WorkflowConfig): EditorState {
  const selected = [...workflow.steps]
    .reverse()
    .find((step) => !isOutput(step));
  return {
    present: { workflow, selectedId: selected?.step_id ?? null },
    past: [],
    future: [],
    saved: JSON.stringify(workflow),
  };
}

export type EditorAction =
  | { type: "load"; workflow: WorkflowConfig }
  | { type: "commit"; snapshot: EditorSnapshot }
  | { type: "select"; id: string | null }
  | { type: "saved"; workflow: WorkflowConfig }
  | { type: "undo" | "redo" };

export function editorReducer(
  state: EditorState,
  action: EditorAction,
): EditorState {
  switch (action.type) {
    case "load":
      return initialEditor(action.workflow);
    case "select":
      return { ...state, present: { ...state.present, selectedId: action.id } };
    case "saved":
      return { ...state, saved: JSON.stringify(action.workflow) };
    case "commit":
      if (
        JSON.stringify(action.snapshot.workflow) ===
        JSON.stringify(state.present.workflow)
      )
        return state;
      return {
        ...state,
        past: [...state.past, state.present].slice(-100),
        present: action.snapshot,
        future: [],
      };
    case "undo": {
      const previous = state.past.at(-1);
      return previous
        ? {
            ...state,
            past: state.past.slice(0, -1),
            present: previous,
            future: [state.present, ...state.future],
          }
        : state;
    }
    case "redo": {
      const next = state.future[0];
      return next
        ? {
            ...state,
            past: [...state.past, state.present],
            present: next,
            future: state.future.slice(1),
          }
        : state;
    }
  }
}

export function isOutput(step: StepConfig): boolean {
  return ["write_csv", "write_excel", "__inspect_frame"].includes(step.key);
}

export function insertSteps(
  snapshot: EditorSnapshot,
  steps: StepConfig[],
): EditorSnapshot {
  const index = snapshot.workflow.steps.findIndex(
    (step) => step.step_id === snapshot.selectedId,
  );
  const next = [...snapshot.workflow.steps];
  next.splice(index < 0 ? next.length : index + 1, 0, ...steps);
  return {
    workflow: { ...snapshot.workflow, steps: next },
    selectedId: steps.at(-1)?.step_id ?? snapshot.selectedId,
  };
}

export function valueExpression(value: unknown, dtype?: string) {
  const valueType = dtype?.startsWith("Datetime")
    ? "datetime"
    : dtype === "Date"
      ? "date"
      : dtype === "Time"
        ? "time"
        : null;
  return valueType && value !== null
    ? { value, value_type: valueType }
    : { value };
}

export function valueCondition(
  column: string,
  value: unknown,
  dtype?: string,
  exclude = false,
) {
  return value === null
    ? { left: { column }, operator: exclude ? "is_not_null" : "is_null" }
    : {
        left: { column },
        operator: exclude ? "!=" : "=",
        right: valueExpression(value, dtype),
      };
}

export function displayValue(value: unknown): string {
  if (value === null || value === undefined) return "(null)";
  if (value === "") return "(empty text)";
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

export function stepSummary(step: StepConfig): string {
  if (step.key === "filter_rows")
    return `${step.name || "Filter"}: ${summarizeCondition(step.parameters.condition)}`;
  if (step.key === "read_workflow")
    return `${step.name || "Workflow"}: ${String(step.parameters.workflow_name ?? "Choose workflow")}`;
  const columns =
    step.parameters.columns ?? step.parameters.column ?? step.parameters.by;
  return columns
    ? `${step.name || step.key}: ${Array.isArray(columns) ? columns.map((item) => (typeof item === "object" ? JSON.stringify(item) : String(item))).join(", ") : String(columns)}`
    : step.name || step.key;
}

export function contextSources(
  workflow: WorkflowConfig,
  anchorId: string | null,
): StepConfig[] {
  const sources = new Map<string, StepConfig>();
  const index = workflow.steps.findIndex((step) => step.step_id === anchorId);
  for (const step of workflow.steps.slice(0, index + 1)) {
    if (
      step.parameters.context_store === true &&
      typeof step.parameters.context_key === "string"
    ) {
      sources.set(step.parameters.context_key, step);
    }
    if (step.key === "join")
      sources.delete(String(step.parameters.right_context_key ?? "right"));
    if (step.key === "concat") {
      const keys = step.parameters.context_keys;
      if (Array.isArray(keys))
        keys.forEach((key) => sources.delete(String(key)));
      else sources.clear();
    }
  }
  return [...sources.values()];
}

function summarizeCondition(value: unknown): string {
  if (!value || typeof value !== "object") return "Configure conditions";
  const condition = value as Record<string, unknown>;
  if (Array.isArray(condition.conditions))
    return condition.conditions
      .map(summarizeCondition)
      .join(` ${String(condition.logic).toUpperCase()} `);
  if (condition.logic === "not")
    return `NOT (${summarizeCondition(condition.condition)})`;
  const left = condition.left as { column?: string } | undefined;
  const right = condition.right as { value?: unknown } | undefined;
  return `${left?.column ?? "expression"} ${String(condition.operator)}${right ? ` ${displayValue(right.value)}` : ""}`;
}

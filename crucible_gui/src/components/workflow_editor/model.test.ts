import { describe, expect, it } from "vitest";
import type { StepConfig, WorkflowConfig } from "@/types/workflows";
import {
  contextSources,
  editorReducer,
  initialEditor,
  insertSteps,
  valueCondition,
} from "./model";
import { createActionStep } from "./actions";

function step(
  id: string,
  key = "read_csv",
  parameters: Record<string, unknown> = {},
): StepConfig {
  return {
    step_id: id,
    key,
    name: id,
    description: "",
    parameters,
    custom_field: "preserved",
  };
}

describe("workflow draft history", () => {
  const workflow: WorkflowConfig = {
    name: "example",
    extra: "keep",
    steps: [
      step("source"),
      step("sort", "sort_rows"),
      step("write", "write_csv"),
    ],
  };

  it("selects the last data-producing step", () => {
    expect(initialEditor(workflow).present.selectedId).toBe("sort");
    expect(
      initialEditor({ name: "empty", steps: [] }).present.selectedId,
    ).toBeNull();
  });

  it("inserts compound source/action edits after selection and restores them atomically", () => {
    let state = editorReducer(initialEditor(workflow), {
      type: "select",
      id: "source",
    });
    const snapshot = insertSteps(state.present, [
      step("right"),
      step("join", "join"),
    ]);
    state = editorReducer(state, { type: "commit", snapshot });
    expect(state.present.workflow.steps.map((item) => item.step_id)).toEqual([
      "source",
      "right",
      "join",
      "sort",
      "write",
    ]);
    expect(state.present.selectedId).toBe("join");
    expect(state.present.workflow.extra).toBe("keep");
    expect(state.present.workflow.steps[0].custom_field).toBe("preserved");
    state = editorReducer(state, { type: "undo" });
    expect(state.present.workflow).toEqual(workflow);
    expect(state.present.selectedId).toBe("source");
    expect(JSON.stringify(state.present.workflow)).toBe(state.saved);
    state = editorReducer(state, { type: "redo" });
    expect(state.present).toEqual(snapshot);
  });

  it("tracks saved state across undo and discards redo after a new edit", () => {
    let state = initialEditor(workflow);
    const snapshot = insertSteps(state.present, [
      step("filter", "filter_rows"),
    ]);
    state = editorReducer(state, { type: "commit", snapshot });
    state = editorReducer(state, {
      type: "saved",
      workflow: snapshot.workflow,
    });
    state = editorReducer(state, { type: "undo" });
    expect(JSON.stringify(state.present.workflow)).not.toBe(state.saved);
    state = editorReducer(state, {
      type: "commit",
      snapshot: insertSteps(state.present, [step("new")]),
    });
    expect(state.future).toEqual([]);
  });
});

describe("table actions", () => {
  it("creates ordinary steps with column context and correct sort direction", () => {
    const sort = createActionStep("sort_desc", ["amount"], [], {
      amount: "Int64",
    });
    expect(sort.key).toBe("sort_rows");
    expect(sort.parameters.columns).toEqual([
      { name: "amount", direction: "desc" },
    ]);
    expect(createActionStep("tail_rows", [], [], {}).parameters).toEqual({
      limit: 10,
      mode: "tail",
    });
  });

  it("preserves temporal types and separates null from empty text", () => {
    expect(valueCondition("date", "2026-11-13", "Date")).toEqual({
      left: { column: "date" },
      operator: "=",
      right: { value: "2026-11-13", value_type: "date" },
    });
    expect(valueCondition("name", null, undefined, true).operator).toBe(
      "is_not_null",
    );
    expect(valueCondition("name", "").operator).toBe("=");
    expect(valueCondition("active", false).right).toEqual({ value: false });
  });

  it("offers only unconsumed context sources", () => {
    const workflow = {
      name: "sources",
      steps: [
        step("primary"),
        step("one", "read_csv", { context_store: true, context_key: "one" }),
        step("two", "read_workflow", {
          context_store: true,
          context_key: "two",
        }),
        step("join", "join", { right_context_key: "one" }),
      ],
    };
    expect(
      contextSources(workflow, "join").map((item) => item.step_id),
    ).toEqual(["two"]);
    workflow.steps.push(step("append", "concat", { context_keys: ["two"] }));
    expect(contextSources(workflow, "append")).toEqual([]);
  });
});

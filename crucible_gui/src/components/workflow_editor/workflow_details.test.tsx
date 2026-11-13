import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { MantineProvider } from "@mantine/core";

vi.mock("@mantine/core", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@mantine/core")>();
  const { TestMenu, TestOverlay, TestSelect, TestScroll, TestCombobox } =
    await import("@/test/layout_mocks");
  return {
    ...actual,
    Menu: TestMenu,
    Drawer: TestOverlay,
    Modal: TestOverlay,
    Select: TestSelect,
    SegmentedControl: TestSelect,
    ScrollArea: TestScroll,
    Combobox: TestCombobox,
  };
});

vi.mock("@/context/api_context", async () => {
  const { createContext } = await import("react");
  return {
    ClientContext: createContext(null),
    SchemaContext: createContext([]),
  };
});
vi.mock("@/components/workflow_graph", () => ({
  WorkflowGraph: ({
    steps,
    onSelect,
  }: {
    steps: { step_id: string; name: string }[];
    onSelect: (step: unknown) => void;
  }) => (
    <div>
      {steps.map((step) => (
        <button key={step.step_id} onClick={() => onSelect(step)}>
          Graph: {step.name}
        </button>
      ))}
    </div>
  ),
}));

import { ClientContext, SchemaContext } from "@/context/api_context";
import type { CrucibleClient } from "@/api/crucibleClient";
import type { DraftPreview, WorkflowConfig } from "@/types/workflows";
import type { StepSchema } from "@/types/step_schema";
import { WorkflowDetails } from "@/components/workflow_details";

const schemas: StepSchema[] = [
  {
    key: "read_csv",
    default_name: "Source",
    default_description: "Read",
    required: [],
    properties: [],
  },
  {
    key: "filter_rows",
    default_name: "Filter",
    default_description: "Filter rows",
    required: [],
    properties: [],
  },
  {
    key: "sort_rows",
    default_name: "Sort",
    default_description: "Sort rows",
    required: [],
    properties: [],
  },
];
const source = {
  step_id: "source",
  key: "read_csv",
  name: "Source",
  description: "Read",
  parameters: { path: "data.csv" },
};
const sorted = {
  step_id: "sorted",
  key: "sort_rows",
  name: "Sorted",
  description: "Sort",
  parameters: { columns: [{ name: "id", direction: "desc" }] },
};
let workflow: WorkflowConfig;
let client: {
  getWorkflow: ReturnType<typeof vi.fn>;
  previewDraft: ReturnType<typeof vi.fn>;
  filterValues: ReturnType<typeof vi.fn>;
  updateWorkflow: ReturnType<typeof vi.fn>;
  runWorkflow: ReturnType<typeof vi.fn>;
};

function preview(id: string, value: number): DraftPreview {
  return {
    data: [{ id: value }],
    columns: ["id"],
    frame_schema: { id: "Int64" },
    input_schema: { id: "Int64" },
    step_id: id,
    truncated: false,
    row_count: 1,
  };
}

function mount() {
  const router = createMemoryRouter(
    [
      {
        path: "/workflows/example",
        element: <WorkflowDetails selectedWorkflow="example" />,
      },
      { path: "/workflows", element: <div>Workflow listing</div> },
    ],
    { initialEntries: ["/workflows/example"] },
  );
  render(
    <MantineProvider
      env="test"
      theme={{
        components: {
          Menu: { defaultProps: { trapFocus: false } },
          Drawer: { defaultProps: { trapFocus: false } },
          Modal: { defaultProps: { trapFocus: false } },
        },
      }}
    >
      <ClientContext.Provider value={client as unknown as CrucibleClient}>
        <SchemaContext.Provider value={schemas}>
          <RouterProvider router={router} />
        </SchemaContext.Provider>
      </ClientContext.Provider>
    </MantineProvider>,
  );
  return router;
}

beforeEach(() => {
  workflow = {
    name: "example",
    steps: [structuredClone(source), structuredClone(sorted)],
  };
  client = {
    getWorkflow: vi.fn().mockImplementation(() =>
      Promise.resolve({
        name: "example",
        path: "example.yaml",
        content: workflow,
      }),
    ),
    previewDraft: vi
      .fn()
      .mockImplementation(
        (_name: string, _workflow: WorkflowConfig, id: string) =>
          Promise.resolve(preview(id, id === "source" ? 0 : 299)),
      ),
    filterValues: vi.fn().mockResolvedValue({
      values: [299, null, ""],
      value_type: "Int64",
      truncated: false,
    }),
    updateWorkflow: vi.fn().mockResolvedValue({}),
    runWorkflow: vi.fn().mockResolvedValue({ success: true }),
  };
});

describe("table-centered workflow editor", () => {
  it("creates a real filter from the column menu, inserts after selection, and supports atomic undo/redo", async () => {
    mount();
    await screen.findByLabelText("id: 299");
    fireEvent.click(screen.getByText(/1\. read_csv/));
    await screen.findByLabelText("id: 0");
    fireEvent.click(screen.getByLabelText("Actions for id"));
    fireEvent.click(await screen.findByText("Filter rows…"));
    const drawer = (await screen.findByText("Add transformation")).closest(
      '[role="dialog"]',
    ) as HTMLElement;
    fireEvent.click(within(drawer).getByLabelText("Values to keep"));
    fireEvent.click(await within(drawer).findByText("299"));
    fireEvent.click(within(drawer).getByText("Apply"));
    await screen.findByText("Unsaved");
    fireEvent.click(screen.getByText("Save"));
    await waitFor(() => expect(client.updateWorkflow).toHaveBeenCalled());
    const saved = client.updateWorkflow.mock.calls[0][1] as WorkflowConfig;
    expect(saved.steps.map((step) => step.key)).toEqual([
      "read_csv",
      "filter_rows",
      "sort_rows",
    ]);
    expect(saved.steps[1].parameters.condition).toEqual({
      left: { column: "id" },
      operator: "=",
      right: { value: 299 },
    });
    fireEvent.click(screen.getByLabelText("Undo"));
    expect(screen.queryByText("Filter: id = 299")).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Redo"));
    expect(screen.getByText("Filter: id = 299")).toBeInTheDocument();
    expect(screen.queryByText("Unsaved")).not.toBeInTheDocument();
  });

  it("cancels an action without changing the draft", async () => {
    mount();
    await screen.findByLabelText("id: 299");
    fireEvent.click(screen.getByLabelText("Actions for id"));
    fireEvent.click(await screen.findByText("Filter rows…"));
    const drawer = (await screen.findByText("Add transformation")).closest(
      '[role="dialog"]',
    ) as HTMLElement;
    fireEvent.click(within(drawer).getByLabelText("Values to keep"));
    fireEvent.click(await within(drawer).findByText("299"));
    fireEvent.click(within(drawer).getByText("Cancel"));
    expect(screen.queryByText("Unsaved")).not.toBeInTheDocument();
    expect(client.updateWorkflow).not.toHaveBeenCalled();
  });

  it("blocks navigation and prevents Run after a failed Save", async () => {
    mount();
    await screen.findByLabelText("id: 299");
    fireEvent.click(screen.getByLabelText("Delete step 2"));
    client.updateWorkflow.mockRejectedValue(new Error("disk full"));
    fireEvent.click(screen.getByText("Run workflow"));
    await waitFor(() => expect(client.updateWorkflow).toHaveBeenCalled());
    await waitFor(() =>
      expect(screen.getByText("Run workflow")).not.toHaveAttribute(
        "data-loading",
      ),
    );
    expect(client.runWorkflow).not.toHaveBeenCalled();
    fireEvent.click(screen.getByLabelText("Back to workflows"));
    await screen.findByText("Discard unsaved changes?");
    fireEvent.click(screen.getByText("Keep editing"));
    expect(screen.queryByText("Workflow listing")).not.toBeInTheDocument();
  });

  it("discards obsolete preview responses and synchronizes graph selection", async () => {
    let resolveOld: (value: DraftPreview) => void = () => {};
    client.previewDraft.mockImplementationOnce(
      () =>
        new Promise<DraftPreview>((resolve) => {
          resolveOld = resolve;
        }),
    );
    mount();
    await waitFor(() => expect(client.previewDraft).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByText("Graph"));
    fireEvent.click(await screen.findByText("Graph: Source"));
    await waitFor(() => expect(client.previewDraft).toHaveBeenCalledTimes(2));
    await screen.findByLabelText("id: 0");
    resolveOld(preview("sorted", 999));
    await waitFor(() =>
      expect(screen.queryByLabelText("id: 999")).not.toBeInTheDocument(),
    );
    expect(screen.getByText(/Preview through Source/)).toBeInTheDocument();
  });
});

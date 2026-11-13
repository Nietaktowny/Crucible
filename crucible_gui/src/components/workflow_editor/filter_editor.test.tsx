import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MantineProvider } from "@mantine/core";

vi.mock("@/context/api_context", async () => {
  const { createContext } = await import("react");
  return {
    ClientContext: createContext(null),
    SchemaContext: createContext([]),
  };
});
vi.mock("@mantine/core", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@mantine/core")>();
  const { TestSelect, TestScroll, TestCombobox } =
    await import("@/test/layout_mocks");
  return {
    ...actual,
    Select: TestSelect,
    SegmentedControl: TestSelect,
    ScrollArea: TestScroll,
    Combobox: TestCombobox,
  };
});

import { ClientContext } from "@/context/api_context";
import type { CrucibleClient } from "@/api/crucibleClient";
import { FilterEditor } from "./filter_editor";

function mount(value?: unknown, schema = { name: "String" }, before = false) {
  const onChange = vi.fn();
  const filterValues = vi.fn().mockResolvedValue({
    values: [null, "", "a.b"],
    truncated: false,
    value_type: "String",
  });
  render(
    <MantineProvider env="test">
      <ClientContext.Provider
        value={{ filterValues } as unknown as CrucibleClient}
      >
        <FilterEditor
          workflowName="sample"
          workflow={{ name: "sample", steps: [] }}
          targetId="selected"
          before={before}
          schema={schema}
          value={value}
          onChange={onChange}
        />
      </ClientContext.Provider>
    </MantineProvider>,
  );
  return { onChange, filterValues };
}

describe("filter authoring", () => {
  it("keeps large selections compact and preserves them across dropdown searches", async () => {
    const existing = Array.from({ length: 300 }, (_, index) => `item-${index}`);
    const { filterValues, onChange } = mount({
      logic: "or",
      conditions: existing.map((value) => ({
        left: { column: "name" },
        operator: "=",
        right: { value },
      })),
    });
    expect(screen.getByLabelText("Values to keep")).toHaveTextContent(
      "300 values selected",
    );
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(screen.queryByText("item-1")).not.toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Values to keep"));
    await screen.findByText("a.b");
    filterValues.mockResolvedValue({
      values: ["found"],
      truncated: false,
      value_type: "String",
    });
    fireEvent.change(screen.getByLabelText("Search all data values"), {
      target: { value: "found" },
    });
    fireEvent.click(await screen.findByText("found"));
    const condition = onChange.mock.lastCall?.[0];
    expect(condition.conditions).toHaveLength(301);
    expect(condition.conditions[0].right.value).toBe("item-0");
    expect(condition.conditions[300].right.value).toBe("found");
    expect(screen.getByLabelText("Values to keep")).toHaveTextContent(
      "301 values selected",
    );

    fireEvent.keyDown(screen.getByLabelText("Search all data values"), {
      key: "Escape",
    });
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Values to keep")).toHaveTextContent(
      "301 values selected",
    );
  });

  it("keeps null and empty text distinct and queries a filter's input", async () => {
    const { filterValues, onChange } = mount(
      undefined,
      { name: "String" },
      true,
    );
    fireEvent.click(screen.getByLabelText("Values to keep"));
    fireEvent.click(await screen.findByText("(null)"));
    expect(onChange).toHaveBeenLastCalledWith({
      left: { column: "name" },
      operator: "is_null",
    });
    fireEvent.click(screen.getByText("(empty text)"));
    expect(onChange).toHaveBeenLastCalledWith({
      logic: "or",
      conditions: [
        { left: { column: "name" }, operator: "is_null" },
        { left: { column: "name" }, operator: "=", right: { value: "" } },
      ],
    });
    expect(filterValues.mock.calls[0][5]).toBe(true);
  });

  it("escapes simple contains text without changing advanced regex conditions", async () => {
    const { onChange } = mount();
    fireEvent.change(screen.getAllByRole("combobox")[0], {
      target: { value: "conditions" },
    });
    fireEvent.change(screen.getByLabelText("Operator"), {
      target: { value: "contains" },
    });
    fireEvent.change(screen.getByLabelText("Value"), {
      target: { value: "a.b" },
    });
    await waitFor(() =>
      expect(onChange).toHaveBeenLastCalledWith({
        left: { column: "name" },
        operator: "contains",
        right: { value: "a\\.b" },
      }),
    );
  });

  it("retains existing regex filters until explicitly edited", () => {
    const condition = {
      left: { column: "name" },
      operator: "contains",
      right: { value: "a.b" },
    };
    const { onChange } = mount(condition);
    expect(screen.getAllByRole("combobox")[0]).toHaveValue("advanced");
    expect(onChange).not.toHaveBeenCalled();
  });
});

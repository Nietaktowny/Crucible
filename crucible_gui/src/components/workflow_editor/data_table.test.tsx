import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MantineProvider } from "@mantine/core";

vi.mock("@mantine/core", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@mantine/core")>();
  const { TestMenu } = await import("@/test/layout_mocks");
  return { ...actual, Menu: TestMenu };
});

import { DataTable } from "./data_table";

describe("workflow data table", () => {
  it("preserves explicit server column order for numeric column names", () => {
    render(
      <MantineProvider env="test">
        <DataTable
          data={[]}
          schema={{ "1": "String", "2": "Int64" }}
          columnOrder={["2", "1"]}
          selectedColumns={[]}
          onSelectColumns={vi.fn()}
          onAction={vi.fn()}
          onFilters={vi.fn()}
          filterColumns={[]}
          disabled={false}
        />
      </MantineProvider>,
    );
    const headers = screen.getAllByRole("columnheader");
    expect(headers[1]).toHaveTextContent("2");
    expect(headers[2]).toHaveTextContent("1");
  });
  it("retains ordered schema headers for empty results", () => {
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
        <DataTable
          data={[]}
          schema={{ amount: "Int64", name: "String" }}
          selectedColumns={[]}
          onSelectColumns={vi.fn()}
          onAction={vi.fn()}
          onFilters={vi.fn()}
          filterColumns={[]}
          disabled={false}
        />
      </MantineProvider>,
    );
    expect(
      screen.getByRole("columnheader", { name: /amount/ }),
    ).toBeInTheDocument();
    expect(screen.getByText("No preview rows returned.")).toBeInTheDocument();
  });

  it("exposes accessible column selection and cell transformation actions", async () => {
    const onSelect = vi.fn();
    const onAction = vi.fn();
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
        <DataTable
          data={[{ name: "" }]}
          schema={{ name: "String" }}
          selectedColumns={[]}
          onSelectColumns={onSelect}
          onAction={onAction}
          onFilters={vi.fn()}
          filterColumns={[]}
          disabled={false}
        />
      </MantineProvider>,
    );
    fireEvent.click(screen.getByLabelText("Select column name"));
    expect(onSelect).toHaveBeenCalledWith(["name"]);
    fireEvent.click(screen.getByLabelText("name: (empty text)"));
    fireEvent.click(screen.getByText("Keep this value…"));
    expect(onAction).toHaveBeenCalledWith("keep_value", ["name"], "");
  });
});

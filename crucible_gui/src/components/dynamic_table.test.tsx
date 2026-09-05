import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MantineProvider } from "@mantine/core";

import { DynamicTable } from "./dynamic_table";

function renderTable(data: Record<string, unknown>[]) {
  return render(
    <MantineProvider>
      <DynamicTable data={data} />
    </MantineProvider>,
  );
}

describe("DynamicTable", () => {
  it("renders an empty state when there are no rows", () => {
    renderTable([]);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders the union of all row keys as columns", () => {
    renderTable([
      { a: 1, b: 2 },
      { b: 3, c: 4 },
    ]);

    expect(screen.getByRole("columnheader", { name: "a" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "b" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "c" })).toBeInTheDocument();
  });

  it("renders missing values as blank cells rather than 'undefined'", () => {
    renderTable([{ a: 1 }, { b: 2 }]);
    expect(screen.queryByText("undefined")).not.toBeInTheDocument();
  });

  it("stringifies cell values", () => {
    renderTable([{ count: 42, active: true }]);
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("true")).toBeInTheDocument();
  });
});

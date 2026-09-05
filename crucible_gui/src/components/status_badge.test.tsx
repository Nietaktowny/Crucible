import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MantineProvider } from "@mantine/core";

import { StatusBadge } from "./status_badge";
import type { WorkflowStatus } from "@/types/workflows";

function renderBadge(status: WorkflowStatus) {
  render(
    <MantineProvider>
      <StatusBadge status={status} />
    </MantineProvider>,
  );
}

describe("StatusBadge", () => {
  it("renders a human-readable label for each known status", () => {
    const cases: Array<[WorkflowStatus, string]> = [
      ["success", "Success"],
      ["failed", "Failed"],
      ["running", "Running"],
      ["waiting", "Waiting"],
      ["created", "Created"],
      ["cancelled", "Cancelled"],
    ];

    for (const [status, label] of cases) {
      const { unmount } = render(
        <MantineProvider>
          <StatusBadge status={status} />
        </MantineProvider>,
      );

      expect(screen.getByText(label)).toBeInTheDocument();
      unmount();
    }
  });

  it("falls back to the 'created' presentation for an unrecognized status", () => {
    // Simulates a future backend status value the frontend doesn't know about yet.
    renderBadge("unknown-status" as WorkflowStatus);
    expect(screen.getByText("Created")).toBeInTheDocument();
  });
});

import { afterEach, describe, expect, it, vi } from "vitest";
import YAML from "yaml";

import { CrucibleClient } from "@/api/crucibleClient";
import type { WorkflowConfig } from "@/types/workflows";
import { serializeWorkflow } from "./workflow_yaml";

const workflow: WorkflowConfig = {
  name: "example",
  steps: [
    {
      step_id: "filter",
      key: "filter_rows",
      name: "Filter",
      description: "",
      parameters: {
        condition: {
          left: { column: "Quantity" },
          operator: "=",
          right: { value: 1 },
        },
        literals: [
          "yes",
          "no",
          "on",
          "off",
          "2026-11-13",
          "12:30:00",
          "",
          "null",
          null,
          true,
          false,
          42,
        ],
      },
    },
  ],
};

afterEach(() => vi.unstubAllGlobals());

describe("workflow YAML serialization", () => {
  it("quotes equality operators and preserves literal types under YAML 1.1 parsing", () => {
    const content = serializeWorkflow(workflow);
    expect(content).toContain('"operator": "="');
    expect(YAML.parse(content, { version: "1.1" })).toEqual(workflow);
  });

  it.each(["create", "update"])(
    "uses safe serialization for %s requests",
    async (operation) => {
      const fetchMock = vi
        .fn()
        .mockResolvedValue({
          ok: true,
          json: async () => ({ content: workflow }),
        });
      vi.stubGlobal("fetch", fetchMock);
      const client = new CrucibleClient();
      if (operation === "create")
        await client.createWorkflow("example", workflow);
      else await client.updateWorkflow("example", workflow);
      const body = JSON.parse(fetchMock.mock.calls[0][1].body);
      expect(body.content).toBe(serializeWorkflow(workflow));
    },
  );
});

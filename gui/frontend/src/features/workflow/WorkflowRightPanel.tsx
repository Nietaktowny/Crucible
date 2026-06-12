import { useState } from "react";

import { Button } from "@/components/ui/button";
import WorkflowGraph from "@/features/workflow/WorkflowGraph";
import WorkflowPreview from "@/features/workflow/WorkflowPreview";
import WorkflowResultPreview from "@/features/workflow/WorkflowResultPreview";
import type { Workflow } from "@/features/workflow/types";
import type { WorkflowRunResponse } from "@/lib/crucibleApi";

type WorkflowRightPanelProps = {
  workflow: Workflow;
  selectedStepId: string | null;
  onSelectStep: (stepId: string | null) => void;
  runResult: WorkflowRunResponse | null;
};

export default function WorkflowRightPanel({
  workflow,
  selectedStepId,
  onSelectStep,
  runResult,
}: WorkflowRightPanelProps) {
  const [view, setView] = useState<"graph" | "yaml" | "preview">("graph");

  return (
    <section className="flex min-h-0 flex-col rounded-lg border bg-card">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h2 className="text-sm font-semibold">
          {view === "graph"
            ? "Workflow Graph"
            : view === "yaml"
              ? "Workflow YAML"
              : "Workflow Preview"}
        </h2>

        <div className="flex gap-2">
          <Button
            size="sm"
            variant={view === "graph" ? "default" : "outline"}
            onClick={() => setView("graph")}
          >
            Graph
          </Button>

          <Button
            size="sm"
            variant={view === "yaml" ? "default" : "outline"}
            onClick={() => setView("yaml")}
          >
            YAML
          </Button>

          <Button
            size="sm"
            variant={view === "preview" ? "default" : "outline"}
            onClick={() => setView("preview")}
          >
            Preview
          </Button>
        </div>
      </div>

      <div className="min-h-0 flex-1">
        {view === "graph" ? (
          <WorkflowGraph
            workflow={workflow}
            selectedStepId={selectedStepId}
            onSelectStep={onSelectStep}
          />
        ) : view === "yaml" ? (
          <WorkflowPreview workflow={workflow} />
        ) : (
          <WorkflowResultPreview
            preview={runResult?.preview ?? null}
            rowCount={runResult?.row_count ?? null}
          />
        )}
      </div>
    </section>
  );
}
import { useState } from "react";

import { Button } from "@/components/ui/button";
import WorkflowGraph from "@/features/workflow/WorkflowGraph";
import WorkflowPreview from "@/features/workflow/WorkflowPreview";
import type { Workflow } from "@/features/workflow/types";

type WorkflowRightPanelProps = {
  workflow: Workflow;
  selectedStepId: string | null;
  onSelectStep: (stepId: string | null) => void;
};

export default function WorkflowRightPanel({
  workflow,
  selectedStepId,
  onSelectStep,
}: WorkflowRightPanelProps) {
  const [view, setView] = useState<"graph" | "yaml">("graph");

  return (
    <section className="flex min-h-0 flex-col rounded-lg border bg-card">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h2 className="text-sm font-semibold">
          {view === "graph" ? "Workflow Graph" : "Workflow YAML"}
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
        </div>
      </div>

      <div className="min-h-0 flex-1">
        {view === "graph" ? (
          <WorkflowGraph
            workflow={workflow}
            selectedStepId={selectedStepId}
            onSelectStep={onSelectStep}
          />
        ) : (
          <WorkflowPreview workflow={workflow} />
        )}
      </div>
    </section>
  );
}
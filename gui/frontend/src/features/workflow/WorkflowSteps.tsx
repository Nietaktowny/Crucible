import { Button } from "@/components/ui/button";
import type { WorkflowStep } from "@/features/workflow/types";

type WorkflowStepsProps = {
  steps: WorkflowStep[];
  selectedStepId: string | null;
  onSelectStep: (stepId: string) => void;
  onRemoveStep: (stepId: string) => void;
};

export default function WorkflowSteps({
  steps,
  selectedStepId,
  onSelectStep,
  onRemoveStep,
}: WorkflowStepsProps) {
  return (
    <section className="flex min-h-0 flex-col rounded-lg border bg-card">
      <div className="border-b px-4 py-3">
        <h2 className="text-sm font-semibold">Workflow Steps</h2>
      </div>

      <div className="min-h-0 flex-1 space-y-2 overflow-auto p-3">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={[
              "flex items-center gap-2 rounded-md border p-2",
              step.id === selectedStepId
                ? "border-primary bg-primary/10"
                : "bg-background",
            ].join(" ")}
          >
            <button
              className="min-w-0 flex-1 text-left"
              onClick={() => onSelectStep(step.id)}
            >
              <div className="truncate text-sm font-medium">
                {String(index + 1).padStart(2, "0")} · {step.name}
              </div>

              <div className="truncate text-xs text-muted-foreground">
                {step.key}
              </div>
            </button>

            <Button
              variant="ghost"
              size="sm"
              className="h-8 px-2 text-muted-foreground hover:text-destructive"
              onClick={() => onRemoveStep(step.id)}
            >
              Remove
            </Button>
          </div>
        ))}
      </div>
    </section>
  );
}
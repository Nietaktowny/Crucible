import { useMemo, useRef, useState } from "react";
import { parse } from "yaml";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import StepConfigPanel from "@/features/workflow/StepConfigPanel";
import StepLibrary from "@/features/workflow/StepLibrary";
import WorkflowRightPanel from "@/features/workflow/WorkflowRightPanel";
import { stepRegistry, type StepKey } from "@/features/workflow/stepRegistry";
import type { Workflow, WorkflowStep } from "@/features/workflow/types";

type LoadedWorkflowStep = {
  key: StepKey;
  name?: string;
  description?: string;
  parameters?: Record<string, unknown>;
};

type LoadedWorkflow = {
  name?: string;
  steps?: LoadedWorkflowStep[];
};

function isStepKey(value: string): value is StepKey {
  return value in stepRegistry;
}

function workflowFromYamlObject(data: LoadedWorkflow): Workflow {
  if (!Array.isArray(data.steps)) {
    throw new Error("Workflow file must contain a steps array.");
  }

  return {
    name: data.name ?? "loaded_workflow",
    steps: data.steps.map((rawStep): WorkflowStep => {
      if (!rawStep.key || !isStepKey(String(rawStep.key))) {
        throw new Error(`Unknown step key: ${String(rawStep.key)}`);
      }

      const definition = stepRegistry[rawStep.key];
      const { key, name, description, parameters = {} } = rawStep;

      return {
        id: crypto.randomUUID(),
        key,
        name: name ?? definition.label,
        description: description ?? definition.description,
        parameters: {
          ...structuredClone(definition.defaultConfig),
          ...parameters,
        },
      };
    }),
  };
}

export default function WorkflowEditorPage() {
  const [darkMode, setDarkMode] = useState(true);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [workflow, setWorkflow] = useState<Workflow>({
    name: "example_workflow",
    steps: [],
  });

  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);

  const selectedStep = useMemo(
    () => workflow.steps.find((step) => step.id === selectedStepId) ?? null,
    [workflow.steps, selectedStepId],
  );

  function addStep(key: StepKey) {
    const definition = stepRegistry[key];

    const newStep: WorkflowStep = {
      id: crypto.randomUUID(),
      key,
      name: definition.label,
      description: definition.description,
      parameters: structuredClone(definition.defaultConfig),
    };

    setWorkflow((current) => {
      if (!selectedStepId) {
        return {
          ...current,
          steps: [...current.steps, newStep],
        };
      }

      const selectedIndex = current.steps.findIndex(
        (step) => step.id === selectedStepId,
      );

      if (selectedIndex === -1) {
        return {
          ...current,
          steps: [...current.steps, newStep],
        };
      }

      return {
        ...current,
        steps: [
          ...current.steps.slice(0, selectedIndex + 1),
          newStep,
          ...current.steps.slice(selectedIndex + 1),
        ],
      };
    });

    setSelectedStepId(newStep.id);
  }

  function updateSelectedStepParameters(field: string, value: unknown) {
    if (!selectedStepId) return;

    setWorkflow((current) => ({
      ...current,
      steps: current.steps.map((step) =>
        step.id === selectedStepId
          ? {
              ...step,
              parameters: {
                ...step.parameters,
                [field]: value,
              },
            }
          : step,
      ),
    }));
  }

  function updateSelectedStepMetadata(
    field: "name" | "description",
    value: string,
  ) {
    if (!selectedStepId) return;

    setWorkflow((current) => ({
      ...current,
      steps: current.steps.map((step) =>
        step.id === selectedStepId
          ? {
              ...step,
              [field]: value,
            }
          : step,
      ),
    }));
  }

  function removeStep(stepId: string) {
    setWorkflow((current) => ({
      ...current,
      steps: current.steps.filter((step) => step.id !== stepId),
    }));

    if (selectedStepId === stepId) {
      setSelectedStepId(null);
    }
  }

  function removeSelectedStep() {
    if (!selectedStepId) return;
    removeStep(selectedStepId);
  }

  async function loadWorkflowFromFile(file: File) {
    const text = await file.text();
    const parsed = parse(text) as LoadedWorkflow;
    const loadedWorkflow = workflowFromYamlObject(parsed);

    setWorkflow(loadedWorkflow);
    setSelectedStepId(loadedWorkflow.steps[0]?.id ?? null);
  }

  async function handleWorkflowFileChange(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];

    if (!file) return;

    try {
      await loadWorkflowFromFile(file);
    } catch (error) {
      console.error(error);
      alert(error instanceof Error ? error.message : "Failed to load workflow.");
    } finally {
      event.target.value = "";
    }
  }

  return (
    <div className={darkMode ? "dark" : ""}>
      <div className="h-screen overflow-hidden bg-background text-foreground">
        <header className="flex h-14 items-center gap-4 border-b px-4">
          <div className="font-semibold">Crucible</div>

          <Separator orientation="vertical" className="h-6" />

          <Input
            className="w-72"
            value={workflow.name}
            onChange={(event) =>
              setWorkflow((current) => ({
                ...current,
                name: event.target.value,
              }))
            }
          />

          <input
            ref={fileInputRef}
            type="file"
            accept=".yaml,.yml"
            className="hidden"
            onChange={handleWorkflowFileChange}
          />

          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
          >
            Load workflow
          </Button>

          <div className="ml-auto">
            <Button
              variant="outline"
              onClick={() => setDarkMode((value) => !value)}
            >
              {darkMode ? "Light mode" : "Dark mode"}
            </Button>
          </div>
        </header>

        <main className="grid h-[calc(100vh-3.5rem)] grid-cols-[280px_380px_minmax(640px,1fr)] gap-4 p-4">
          <StepLibrary onAddStep={addStep} />

          <StepConfigPanel
            step={selectedStep}
            onUpdateParameters={updateSelectedStepParameters}
            onUpdateMetadata={updateSelectedStepMetadata}
            onRemoveStep={removeSelectedStep}
          />

          <WorkflowRightPanel
            workflow={workflow}
            selectedStepId={selectedStepId}
            onSelectStep={setSelectedStepId}
          />
        </main>
      </div>
    </div>
  );
}
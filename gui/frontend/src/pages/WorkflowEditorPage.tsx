import { useEffect, useMemo, useRef, useState } from "react";
import { parse, stringify } from "yaml";

import ErrorPanel from "@/components/ErrorPanel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import StepConfigPanel from "@/features/workflow/StepConfigPanel";
import StepLibrary from "@/features/workflow/StepLibrary";
import WorkflowRightPanel from "@/features/workflow/WorkflowRightPanel";
import { stepRegistry, type StepKey } from "@/features/workflow/stepRegistry";
import {
  isMultiSourceStep,
  type Workflow,
  type WorkflowEditorStep,
  type WorkflowSourceStep,
  type WorkflowStep,
} from "@/features/workflow/types";
import {
  createWorkflow,
  getCachedPreview,
  getWorkflow,
  listStepSchemas,
  listWorkflows,
  runWorkflow,
  updateWorkflow,
  type StepSchemaDefinition,
  type WorkflowRunResponse,
  type WorkflowSummary,
} from "@/lib/crucibleApi";

const MULTI_SOURCE_STEP_KEYS = new Set<StepKey>(["join", "concat"] as StepKey[]);

type LoadedWorkflowStep = {
  key: StepKey;
  name?: string;
  description?: string;
  parameters?: Record<string, unknown>;
  alias?: string;
  sources?: LoadedWorkflowStep[];
};

type LoadedWorkflow = {
  name?: string;
  steps?: LoadedWorkflowStep[];
};

type ErrorWithDetails = Error & {
  details?: unknown;
};

function isStepKey(value: string): value is StepKey {
  return value in stepRegistry;
}

function isMultiSourceStepKey(key: StepKey): boolean {
  return MULTI_SOURCE_STEP_KEYS.has(key);
}

function workflowSourceStepFromYamlObject(
  rawStep: LoadedWorkflowStep,
): WorkflowSourceStep {
  const step = workflowStepFromYamlObject(rawStep);

  const sourceStep: WorkflowSourceStep = {
    id: step.id,
    key: step.key,
    name: step.name,
    description: step.description,
    parameters: step.parameters,
    alias: rawStep.alias,
  };

  if (isMultiSourceStep(step)) {
    sourceStep.sources = step.sources;
  }

  return sourceStep;
}

function workflowStepFromYamlObject(
  rawStep: LoadedWorkflowStep,
): WorkflowEditorStep {
  if (!rawStep.key || !isStepKey(String(rawStep.key))) {
    throw new Error(`Unknown step key: ${String(rawStep.key)}`);
  }

  const definition = stepRegistry[rawStep.key];
  const { key, name, description, parameters = {}, sources } = rawStep;

  const step: WorkflowStep = {
    id: crypto.randomUUID(),
    key,
    name: name ?? definition.label,
    description: description ?? definition.description,
    parameters: {
      ...structuredClone(definition.defaultConfig),
      ...parameters,
    },
  };

  if (Array.isArray(sources)) {
    return {
      ...step,
      sources: sources.map(workflowSourceStepFromYamlObject),
    };
  }

  if (isMultiSourceStepKey(key)) {
    return {
      ...step,
      sources: [],
    };
  }

  return step;
}

function workflowFromYamlObject(data: LoadedWorkflow): Workflow {
  if (!Array.isArray(data.steps)) {
    throw new Error("Workflow file must contain a steps array.");
  }

  return {
    name: data.name ?? "loaded_workflow",
    steps: data.steps.map(workflowStepFromYamlObject),
  };
}

function stepToYamlObject(step: WorkflowEditorStep | WorkflowSourceStep) {
  const result: Record<string, unknown> = {
    key: step.key,
    name: step.name,
    description: step.description,
    parameters: step.parameters,
  };

  if ("alias" in step && step.alias) {
    result.alias = step.alias;
  }

  if (isMultiSourceStep(step)) {
    result.sources = step.sources.map(stepToYamlObject);
  }

  return result;
}

function workflowToYaml(workflow: Workflow): string {
  return stringify(
    {
      name: workflow.name,
      steps: workflow.steps.map(stepToYamlObject),
    },
    {
      defaultStringType: "QUOTE_DOUBLE",
    },
  );
}

function getPreviewColumns(runResult: WorkflowRunResponse | null): string[] {
  const firstRow = runResult?.preview?.[0];

  if (!firstRow) {
    return [];
  }

  return Object.keys(firstRow);
}

export default function WorkflowEditorPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [serverWorkflows, setServerWorkflows] = useState<WorkflowSummary[]>([]);
  const [selectedServerWorkflow, setSelectedServerWorkflow] = useState("");
  const [isLinkedToServer, setIsLinkedToServer] = useState(false);

  const [workflow, setWorkflow] = useState<Workflow>({
    name: "example_workflow",
    steps: [],
  });

  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [runResult, setRunResult] = useState<WorkflowRunResponse | null>(null);

  const [stepSchemas, setStepSchemas] = useState<
    Record<string, StepSchemaDefinition>
  >({});

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<string | undefined>();

  const selectedStep = useMemo(
    () => workflow.steps.find((step) => step.id === selectedStepId) ?? null,
    [workflow.steps, selectedStepId],
  );

  const selectedStepSchema = selectedStep
    ? stepSchemas[selectedStep.key]
    : undefined;

  const previewColumns = useMemo(
    () => getPreviewColumns(runResult),
    [runResult],
  );

  async function refreshServerWorkflows() {
    const result = await listWorkflows();
    setServerWorkflows(result.workflows);
  }

  async function refreshStepSchemas() {
    const schemas = await listStepSchemas();

    setStepSchemas(
      Object.fromEntries(schemas.map((schema) => [schema.key, schema])),
    );
  }

  async function loadCachedPreviewForWorkflow(name: string) {
    const cachedPreview = await getCachedPreview(name);

    if (!cachedPreview) {
      setRunResult(null);
      return false;
    }

    setRunResult({
      workflow_name: name,
      success: true,
      message: "Loaded cached preview.",
      preview: cachedPreview.data,
      row_count: cachedPreview.row_count,
    });

    return true;
  }

  async function loadWorkflowFromServer(name: string) {
    setErrorMessage(null);
    setErrorDetails(undefined);
    setRunResult(null);

    const result = await getWorkflow(name);
    const parsed = parse(result.content) as LoadedWorkflow;
    const loadedWorkflow = workflowFromYamlObject(parsed);

    setWorkflow(loadedWorkflow);
    setSelectedServerWorkflow(result.name);
    setIsLinkedToServer(true);
    setSelectedStepId(loadedWorkflow.steps[0]?.id ?? null);

    const hasCachedPreview = await loadCachedPreviewForWorkflow(result.name);

    setStatus(
      hasCachedPreview
        ? `Loaded ${result.name} with cached preview.`
        : `Loaded ${result.name}. No cached preview.`,
    );
  }

  async function handleServerWorkflowChange(name: string) {
    if (!name) {
      setSelectedServerWorkflow("");
      setRunResult(null);
      return;
    }

    try {
      await loadWorkflowFromServer(name);
    } catch (error) {
      console.error(error);

      const message =
        error instanceof Error ? error.message : "Failed to load workflow.";

      const details = (error as ErrorWithDetails).details;

      setErrorMessage(message);
      setErrorDetails(details ? JSON.stringify(details, null, 2) : undefined);
      setStatus("Failed to load workflow.");
    }
  }

  async function saveWorkflowToServer() {
    setErrorMessage(null);
    setErrorDetails(undefined);
    setRunResult(null);

    const content = workflowToYaml(workflow);

    if (isLinkedToServer && selectedServerWorkflow) {
      await updateWorkflow(selectedServerWorkflow, content);
      setStatus(
        `Saved ${selectedServerWorkflow}. Run workflow to refresh preview.`,
      );
      return;
    }

    const result = await createWorkflow(workflow.name, content);

    setSelectedServerWorkflow(result.name);
    setIsLinkedToServer(true);
    await refreshServerWorkflows();

    setStatus(`Created ${result.name}. Run workflow to create preview.`);
  }

  async function runSelectedWorkflow() {
    if (!selectedServerWorkflow) {
      setStatus("No workflow selected.");
      return;
    }

    setErrorMessage(null);
    setErrorDetails(undefined);
    setRunResult(null);
    setStatus("Running workflow...");

    try {
      const result = await runWorkflow(selectedServerWorkflow, false, true, 200);
      setRunResult(result);
      setStatus(result.message);
    } catch (error) {
      console.error(error);

      const message =
        error instanceof Error ? error.message : "Workflow execution failed.";

      const details = (error as ErrorWithDetails).details;

      setStatus("Workflow failed.");
      setErrorMessage(message);
      setErrorDetails(details ? JSON.stringify(details, null, 2) : undefined);
    }
  }

  useEffect(() => {
    refreshServerWorkflows().catch((error) => {
      console.error(error);
      setStatus(
        error instanceof Error ? error.message : "Failed to load workflows.",
      );
    });

    refreshStepSchemas().catch((error) => {
      console.error(error);
      setStatus(
        error instanceof Error ? error.message : "Failed to load step schemas.",
      );
    });
  }, []);

  function createNewWorkflow() {
    setWorkflow({
      name: "new_workflow",
      steps: [],
    });

    setSelectedServerWorkflow("");
    setIsLinkedToServer(false);
    setSelectedStepId(null);
    setRunResult(null);
    setStatus("New unsaved workflow.");
    setErrorMessage(null);
    setErrorDetails(undefined);
  }

  function createStepFromRegistry(key: StepKey): WorkflowEditorStep {
    const definition = stepRegistry[key];

    const step: WorkflowStep = {
      id: crypto.randomUUID(),
      key,
      name: definition.label,
      description: definition.description,
      parameters: structuredClone(definition.defaultConfig),
    };

    if (isMultiSourceStepKey(key)) {
      return {
        ...step,
        sources: [],
      };
    }

    return step;
  }

  function addStep(key: StepKey) {
    const newStep = createStepFromRegistry(key);

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

  function updateSelectedStepSources(sources: WorkflowSourceStep[]) {
    if (!selectedStepId) return;

    setWorkflow((current) => ({
      ...current,
      steps: current.steps.map((step) =>
        step.id === selectedStepId && isMultiSourceStep(step)
          ? {
              ...step,
              sources,
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

  async function importWorkflowFromFile(file: File) {
    setErrorMessage(null);
    setErrorDetails(undefined);
    setRunResult(null);

    const text = await file.text();
    const parsed = parse(text) as LoadedWorkflow;
    const loadedWorkflow = workflowFromYamlObject(parsed);

    setWorkflow(loadedWorkflow);
    setSelectedServerWorkflow("");
    setIsLinkedToServer(false);
    setSelectedStepId(loadedWorkflow.steps[0]?.id ?? null);
    setStatus(`Imported ${file.name}`);
  }

  async function handleWorkflowFileChange(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];

    if (!file) return;

    try {
      await importWorkflowFromFile(file);
    } catch (error) {
      console.error(error);

      const message =
        error instanceof Error ? error.message : "Failed to import workflow.";

      setErrorMessage(message);
      setErrorDetails(undefined);
      setStatus("Failed to import workflow.");
    } finally {
      event.target.value = "";
    }
  }

  return (
    <div className="h-full overflow-hidden bg-background text-foreground">
      <header className="flex h-14 items-center gap-4 border-b px-4">
        <Input
          className="w-72"
          value={workflow.name}
          onChange={(event) => {
            setWorkflow((current) => ({
              ...current,
              name: event.target.value,
            }));
          }}
        />

        <Button variant="outline" onClick={createNewWorkflow}>
          New
        </Button>

        <select
          className="h-9 rounded-md border bg-background px-3 text-sm"
          value={selectedServerWorkflow}
          onChange={(event) => handleServerWorkflowChange(event.target.value)}
        >
          <option value="">Select workflow</option>
          {serverWorkflows.map((item) => (
            <option key={item.name} value={item.name}>
              {item.name}
            </option>
          ))}
        </select>

        <Button
          variant="outline"
          onClick={() => {
            saveWorkflowToServer().catch((error) => {
              console.error(error);

              const message =
                error instanceof Error ? error.message : "Failed to save workflow.";

              const details = (error as ErrorWithDetails).details;

              setErrorMessage(message);
              setErrorDetails(
                details ? JSON.stringify(details, null, 2) : undefined,
              );
              setStatus("Failed to save workflow.");
            });
          }}
        >
          Save
        </Button>

        <Button variant="outline" onClick={runSelectedWorkflow}>
          Run
        </Button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".yaml,.yml"
          className="hidden"
          onChange={handleWorkflowFileChange}
        />

        <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
          Import
        </Button>

        <div className="ml-auto flex items-center gap-3">
          {status && (
            <div className="max-w-[360px] truncate text-sm text-muted-foreground">
              {status}
            </div>
          )}
        </div>
      </header>

      <main className="grid h-[calc(100%-3.5rem)] grid-cols-[280px_380px_minmax(640px,1fr)] gap-4 p-4">
        <StepLibrary onAddStep={addStep} />

        <StepConfigPanel
          step={selectedStep}
          schema={selectedStepSchema}
          availableColumns={previewColumns}
          onUpdateParameters={updateSelectedStepParameters}
          onUpdateMetadata={updateSelectedStepMetadata}
          onUpdateSources={updateSelectedStepSources}
          onRemoveStep={removeSelectedStep}
        />

        <WorkflowRightPanel
          workflow={workflow}
          selectedStepId={selectedStepId}
          onSelectStep={setSelectedStepId}
          runResult={runResult}
        />
      </main>

      {errorMessage && (
        <ErrorPanel
          title="Workflow error"
          message={errorMessage}
          details={errorDetails}
          onClose={() => {
            setErrorMessage(null);
            setErrorDetails(undefined);
          }}
        />
      )}
    </div>
  );
}
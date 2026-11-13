import { useContext, useEffect, useState } from "react";
import {
  Alert,
  Button,
  Drawer,
  Group,
  Loader,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";

import { ClientContext, SchemaContext } from "@/context/api_context";
import { StepForm } from "@/components/step_editor/step_form";
import { setValueAtPath } from "@/components/step_editor/model";
import type { StepConfig, WorkflowConfig } from "@/types/workflows";
import { getErrorMessage } from "@/lib/format";
import { FilterEditor } from "./filter_editor";
import { CombineEditor } from "./combine_editor";

export type StepDialogDraft = {
  step: StepConfig;
  editing: boolean;
  columns: string[];
  sources: StepConfig[];
  inputSchema: Record<string, string>;
};

type Props = {
  initial: StepDialogDraft;
  workflow: WorkflowConfig;
  workflowName: string;
  selectedId: string | null;
  onClose: () => void;
  onApply: (draft: StepDialogDraft) => void;
};

export function StepSettingsDrawer({
  initial,
  workflow,
  workflowName,
  selectedId,
  onClose,
  onApply,
}: Props) {
  const client = useContext(ClientContext);
  const schemas = useContext(SchemaContext);
  const [draft, setDraft] = useState(initial);
  const [inputSchema, setInputSchema] = useState(initial.inputSchema);
  const index = workflow.steps.findIndex(
    (step) => step.step_id === initial.step.step_id,
  );
  const [loading, setLoading] = useState(initial.editing && index > 0);
  const [error, setError] = useState<string | null>(null);
  const [combineReady, setCombineReady] = useState(false);
  const { step, editing, columns, sources } = draft;
  const schema = schemas.find((item) => item.key === step.key);
  const isCombine = step.key === "join" || step.key === "concat";
  const anchorId = editing
    ? (workflow.steps[index - 1]?.step_id ?? null)
    : selectedId;

  useEffect(() => {
    if (!initial.editing || index <= 0) return;
    const controller = new AbortController();
    void client
      .previewDraft(
        workflowName,
        workflow,
        initial.step.step_id,
        controller.signal,
        true,
      )
      .then((result) => {
        if (!controller.signal.aborted) setInputSchema(result.frame_schema);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(getErrorMessage(reason));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [client, workflowName, workflow, initial, index]);

  function missingFields(item: StepConfig): string[] {
    const definition = schemas.find((candidate) => candidate.key === item.key);
    return (definition?.properties ?? [])
      .filter(
        (field) =>
          field.required &&
          (item.parameters[field.key] === undefined ||
            (item.parameters[field.key] === null && !field.nullable) ||
            item.parameters[field.key] === ""),
      )
      .map((field) => field.title);
  }
  const missing = [step, ...sources].flatMap(missingFields);

  return (
    <Drawer
      opened
      onClose={onClose}
      title={editing ? "Step settings" : "Add transformation"}
      position="right"
      size="lg"
    >
      <Stack gap="md">
        <TextInput
          label="Step name"
          value={step.name ?? ""}
          onChange={(event) =>
            setDraft({
              ...draft,
              step: { ...step, name: event.currentTarget.value },
            })
          }
        />
        <Text size="xs" c="dimmed">
          {step.description}
        </Text>
        {loading && (
          <Group>
            <Loader size="xs" />
            <Text size="xs">Loading input columns…</Text>
          </Group>
        )}
        {error && (
          <Alert color="red" title="Input preview failed">
            {error}
          </Alert>
        )}
        {loading ? null : step.key === "filter_rows" ? (
          <FilterEditor
            workflowName={workflowName}
            workflow={workflow}
            targetId={editing ? step.step_id : selectedId}
            before={editing}
            schema={inputSchema}
            initialColumn={columns[0]}
            value={step.parameters.condition}
            onChange={(condition) =>
              setDraft({
                ...draft,
                step: {
                  ...step,
                  parameters: { ...step.parameters, condition },
                },
              })
            }
          />
        ) : isCombine ? (
          <CombineEditor
            allowLegacy={editing}
            step={step}
            workflow={workflow}
            workflowName={workflowName}
            anchorId={anchorId}
            columns={Object.keys(inputSchema)}
            sources={sources}
            onSources={(next) =>
              setDraft((current) => ({ ...current, sources: next }))
            }
            onChange={(next) =>
              setDraft((current) => ({ ...current, step: next }))
            }
            onReady={setCombineReady}
          />
        ) : schema ? (
          <StepForm
            schema={schema}
            context={{
              stepKey: step.key,
              parameters: step.parameters,
              inputColumns: Object.keys(inputSchema),
              leftColumns: Object.keys(inputSchema),
              rightColumns: [],
              loadSheets: (path) => client.getExcelSheets(path),
            }}
            onChange={(path, value) =>
              setDraft({
                ...draft,
                step: {
                  ...step,
                  parameters: setValueAtPath(step.parameters, path, value),
                },
              })
            }
          />
        ) : (
          <Alert color="red">Step schema unavailable: {step.key}</Alert>
        )}
        {missing.length > 0 && (
          <Text size="xs" c="dimmed">
            Required: {missing.join(", ")}
          </Text>
        )}
        <Group justify="end">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button
            color="ember"
            disabled={
              !schema ||
              missing.length > 0 ||
              (isCombine && !combineReady) ||
              loading
            }
            onClick={() => onApply(draft)}
          >
            Apply
          </Button>
        </Group>
      </Stack>
    </Drawer>
  );
}

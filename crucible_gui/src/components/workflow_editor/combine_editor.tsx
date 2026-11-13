import { useContext, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Group,
  MultiSelect,
  Select,
  Stack,
  Text,
} from "@mantine/core";

import { ClientContext, SchemaContext } from "@/context/api_context";
import { StepForm } from "@/components/step_editor/step_form";
import { setValueAtPath } from "@/components/step_editor/model";
import type { StepConfig, WorkflowConfig } from "@/types/workflows";
import { getErrorMessage } from "@/lib/format";
import { createActionStep } from "./actions";
import { contextSources } from "./model";

type Props = {
  step: StepConfig;
  workflow: WorkflowConfig;
  workflowName: string;
  anchorId: string | null;
  columns: string[];
  sources: StepConfig[];
  onSources: (sources: StepConfig[]) => void;
  onChange: (step: StepConfig) => void;
  onReady: (ready: boolean) => void;
  allowLegacy?: boolean;
};

export function CombineEditor({
  step,
  workflow,
  workflowName,
  anchorId,
  columns,
  sources,
  onSources,
  onChange,
  onReady,
  allowLegacy = false,
}: Props) {
  const client = useContext(ClientContext);
  const schemas = useContext(SchemaContext);
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [sourceKind, setSourceKind] = useState("read_csv");
  const [rightColumns, setRightColumns] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const isJoin = step.key === "join";
  const available = useMemo(
    () => [
      ...contextSources(workflow, anchorId),
      ...(Array.isArray(step.sources)
        ? (step.sources as StepConfig[]).filter(
            (source) =>
              source.parameters.context_store === true &&
              source.parameters.context_key,
          )
        : []),
    ],
    [workflow, anchorId, step.sources],
  );
  const options = useMemo(
    () =>
      available.map((item) => ({
        value: String(item.parameters.context_key),
        label: `${item.name || item.key} (${String(item.parameters.context_key)})`,
      })),
    [available],
  );
  const keys = useMemo(
    () =>
      isJoin
        ? [String(step.parameters.right_context_key ?? "right")]
        : ((step.parameters.context_keys as string[] | undefined) ??
          options.map((item) => item.value)),
    [step.parameters, isJoin, options],
  );
  const primarySource =
    sources[0] ??
    available.find((item) =>
      keys.includes(String(item.parameters.context_key)),
    );
  const combinationSchema = schemas.find((item) => item.key === step.key);

  useEffect(() => {
    let active = true;
    void client
      .getWorkflows()
      .then((items) => {
        if (active)
          setWorkflows(
            items
              .map((item) => item.name)
              .filter((name) => name !== workflowName),
          );
      })
      .catch((reason: unknown) => {
        if (active) setError(getErrorMessage(reason));
      });
    return () => {
      active = false;
    };
  }, [client, workflowName]);

  useEffect(() => {
    if (!primarySource) return;
    const controller = new AbortController();
    const source = {
      ...primarySource,
      parameters: { ...primarySource.parameters, context_store: false },
    };
    const timer = window.setTimeout(() => {
      setError(null);
      void client
        .previewDraft(
          workflowName,
          { name: workflowName, steps: [source] },
          source.step_id,
          controller.signal,
        )
        .then((result) => {
          if (!controller.signal.aborted)
            setRightColumns(Object.keys(result.frame_schema));
        })
        .catch((reason: unknown) => {
          if (!controller.signal.aborted) {
            setError(getErrorMessage(reason));
            setRightColumns([]);
          }
        });
    }, 300);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [primarySource, client, workflowName]);

  useEffect(() => {
    const knownKeys = [
      ...options.map((item) => item.value),
      ...sources.map((item) => String(item.parameters.context_key)),
    ];
    const keyList = (value: unknown) =>
      Array.isArray(value) ? value : typeof value === "string" ? [value] : [];
    const left = keyList(step.parameters.left_on);
    const right = keyList(step.parameters.right_on);
    const validJoin =
      !isJoin ||
      step.parameters.how === "cross" ||
      (left.length > 0 &&
        left.length === right.length &&
        [...left, ...right].every(
          (key) => typeof key === "string" && key.length > 0,
        ));
    onReady(
      validJoin &&
        ((allowLegacy && !isJoin && step.parameters.context_keys == null) ||
          (keys.length > 0 && keys.every((key) => knownKeys.includes(key)))),
    );
  }, [keys, sources, options, onReady, allowLegacy, isJoin, step.parameters]);

  function addSource() {
    const source = createActionStep(sourceKind, [], schemas, {});
    source.parameters = {
      ...source.parameters,
      context_store: true,
      context_key: `source_${crypto.randomUUID()}`,
    };
    const next = isJoin ? [source] : [...sources, source];
    onSources(next);
    onChange({
      ...step,
      parameters: {
        ...step.parameters,
        ...(isJoin
          ? { right_context_key: source.parameters.context_key }
          : { context_keys: [...keys, source.parameters.context_key] }),
      },
    });
  }

  function selectExisting(next: string[]) {
    if (isJoin) onSources([]);
    onChange({
      ...step,
      parameters: {
        ...step.parameters,
        ...(isJoin
          ? { right_context_key: next[0] ?? "" }
          : {
              context_keys: [
                ...next,
                ...sources.map((source) =>
                  String(source.parameters.context_key),
                ),
              ],
            }),
      },
    });
  }

  return (
    <Stack gap="md">
      <Text size="sm">
        Choose a saved workflow, file, folder, or existing source. Source
        loading and this transformation are applied together.
      </Text>
      {isJoin ? (
        <Select
          label="Existing right source"
          data={options}
          value={sources.length ? null : (keys[0] ?? null)}
          onChange={(next) => selectExisting(next ? [next] : [])}
          clearable
        />
      ) : (
        <MultiSelect
          label="Existing append sources"
          data={options}
          value={keys.filter((key) =>
            options.some((option) => option.value === key),
          )}
          onChange={selectExisting}
        />
      )}
      <Group align="end">
        <Select
          label="New source type"
          value={sourceKind}
          onChange={(next) => setSourceKind(next ?? "read_csv")}
          data={[
            { value: "read_csv", label: "CSV file" },
            { value: "read_excel", label: "Excel file" },
            { value: "read_folder_csv", label: "CSV folder" },
            { value: "read_folder_excel", label: "Excel folder" },
            { value: "read_workflow", label: "Saved workflow" },
          ]}
        />
        <Button variant="light" onClick={addSource}>
          {isJoin ? "Set right source" : "Add source"}
        </Button>
      </Group>
      {sources.map((source, index) => {
        const schema = schemas.find((item) => item.key === source.key);
        const update = (next: StepConfig) =>
          onSources(sources.map((item, i) => (i === index ? next : item)));
        return (
          <Stack className="fire-panel" p="sm" key={source.step_id}>
            <Group justify="space-between">
              <Text fw={600} size="sm">
                {source.name}
              </Text>
              <Button
                size="xs"
                variant="subtle"
                color="red"
                onClick={() => {
                  onSources(sources.filter((_, i) => i !== index));
                  onChange({
                    ...step,
                    parameters: {
                      ...step.parameters,
                      ...(isJoin
                        ? { right_context_key: "" }
                        : {
                            context_keys: keys.filter(
                              (key) => key !== source.parameters.context_key,
                            ),
                          }),
                    },
                  });
                }}
              >
                Remove source
              </Button>
            </Group>
            {source.key === "read_workflow" ? (
              <Select
                label="Saved workflow"
                searchable
                data={workflows}
                value={String(source.parameters.workflow_name ?? "")}
                onChange={(next) =>
                  update({
                    ...source,
                    parameters: {
                      ...source.parameters,
                      workflow_name: next ?? "",
                    },
                  })
                }
              />
            ) : (
              schema && (
                <StepForm
                  schema={{
                    ...schema,
                    properties: schema.properties.filter(
                      (field) =>
                        !["context_store", "context_key"].includes(field.key),
                    ),
                  }}
                  context={{
                    stepKey: source.key,
                    parameters: source.parameters,
                    inputColumns: [],
                    leftColumns: [],
                    rightColumns: [],
                    loadSheets: (path) => client.getExcelSheets(path),
                  }}
                  onChange={(path, value) =>
                    update({
                      ...source,
                      parameters: setValueAtPath(
                        source.parameters,
                        path,
                        value,
                      ),
                    })
                  }
                />
              )
            )}
          </Stack>
        );
      })}
      {error && (
        <Alert color="red" title="Source preview">
          {error}
        </Alert>
      )}
      {isJoin && (
        <Text size="xs" c="dimmed">
          Left: {columns.join(", ") || "No columns"} · Right:{" "}
          {rightColumns.join(", ") || "Configure a source to load columns"}
        </Text>
      )}
      {combinationSchema && (
        <StepForm
          schema={{
            ...combinationSchema,
            properties: combinationSchema.properties.filter(
              (field) =>
                !["right_context_key", "context_keys"].includes(field.key),
            ),
          }}
          context={{
            stepKey: step.key,
            parameters: step.parameters,
            inputColumns: columns,
            leftColumns: columns,
            rightColumns,
            loadSheets: (path) => client.getExcelSheets(path),
          }}
          onChange={(path, value) => {
            const parameters = setValueAtPath(step.parameters, path, value);
            if (isJoin && parameters.how === "cross") {
              parameters.left_on ??= [];
              parameters.right_on ??= [];
            }
            onChange({ ...step, parameters });
          }}
        />
      )}
    </Stack>
  );
}

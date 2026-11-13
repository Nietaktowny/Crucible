import {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
} from "react";
import { useBeforeUnload, useBlocker, useNavigate } from "react-router-dom";
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Drawer,
  Group,
  Loader,
  Menu,
  Modal,
  Stack,
  Text,
  Title,
  Tooltip,
  UnstyledButton,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  IconArrowDown,
  IconArrowLeft,
  IconArrowUp,
  IconDeviceFloppy,
  IconEdit,
  IconPlayerPlay,
  IconPlus,
  IconSchema,
  IconTrash,
  IconArrowBackUp,
  IconArrowForwardUp,
} from "@tabler/icons-react";

import type { DraftPreview, StepConfig } from "@/types/workflows";
import { ClientContext, SchemaContext } from "@/context/api_context";
import { WorkflowGraph } from "@/components/workflow_graph";
import { StepLibrary } from "@/components/step_library";
import { getErrorMessage } from "@/lib/format";
import { DataTable } from "@/components/workflow_editor/data_table";
import {
  StepSettingsDrawer,
  type StepDialogDraft,
} from "@/components/workflow_editor/step_settings_drawer";
import {
  createActionStep,
  transformationGroups,
} from "@/components/workflow_editor/actions";
import {
  editorReducer,
  initialEditor,
  insertSteps,
  stepSummary,
} from "@/components/workflow_editor/model";

type Props = { selectedWorkflow: string | null };
type PreviewFailure = { key: string; message: string; stepId?: string };

export function WorkflowDetails({ selectedWorkflow }: Props) {
  const client = useContext(ClientContext);
  const schemas = useContext(SchemaContext);
  const navigate = useNavigate();
  const [editor, dispatch] = useReducer(
    editorReducer,
    { name: "", steps: [] },
    initialEditor,
  );
  const { workflow, selectedId } = editor.present;
  const [loadedName, setLoadedName] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [preview, setPreview] = useState<DraftPreview | null>(null);
  const [previewKey, setPreviewKey] = useState("");
  const [previewError, setPreviewError] = useState<PreviewFailure | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [graphOpen, setGraphOpen] = useState(false);
  const [dialog, setDialog] = useState<StepDialogDraft | null>(null);
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [filterColumn, setFilterColumn] = useState<string | null>(null);
  const requestGeneration = useRef(0);
  const dirty = JSON.stringify(workflow) !== editor.saved;
  const ready = loadedName === selectedWorkflow && loadedName !== null;
  const requestKey = JSON.stringify([
    selectedWorkflow,
    workflow,
    selectedId,
    refresh,
  ]);
  const currentError = previewError?.key === requestKey ? previewError : null;
  const outdated = previewKey !== requestKey;
  const previewBusy =
    ready && selectedId !== null && outdated && currentError === null;
  const selectedStep = workflow.steps.find(
    (step) => step.step_id === selectedId,
  );
  const blocker = useBlocker(dirty || dialog !== null);

  useBeforeUnload(
    useCallback(
      (event) => {
        if (dirty || dialog !== null) {
          event.preventDefault();
          event.returnValue = "";
        }
      },
      [dirty, dialog],
    ),
  );

  useEffect(() => {
    if (!selectedWorkflow) return;
    let active = true;
    void client
      .getWorkflow(selectedWorkflow)
      .then((result) => {
        if (!active) return;
        dispatch({ type: "load", workflow: result.content });
        setLoadedName(selectedWorkflow);
        setPreview(null);
        setPreviewKey("");
        setLoadError(null);
        setSelectedColumns([]);
        setDialog(null);
        setFilterColumn(null);
      })
      .catch((error: unknown) => {
        if (active) setLoadError(getErrorMessage(error));
      });
    return () => {
      active = false;
    };
  }, [client, selectedWorkflow]);

  useEffect(() => {
    const generation = ++requestGeneration.current;
    if (!ready || !selectedWorkflow || !selectedId) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      void client
        .previewDraft(selectedWorkflow, workflow, selectedId, controller.signal)
        .then((result) => {
          if (
            controller.signal.aborted ||
            requestGeneration.current !== generation
          )
            return;
          setPreview(result);
          setPreviewKey(requestKey);
          setPreviewError(null);
          setSelectedColumns((columns) =>
            columns.filter((column) => column in result.frame_schema),
          );
        })
        .catch((error: unknown) => {
          if (
            controller.signal.aborted ||
            requestGeneration.current !== generation
          )
            return;
          const cause =
            error instanceof Error
              ? (error.cause as
                  { step_id?: string; workflow_name?: string } | undefined)
              : undefined;
          setPreviewError({
            key: requestKey,
            message: `${cause?.workflow_name && cause.workflow_name !== workflow.name ? `In workflow ${cause.workflow_name}: ` : ""}${getErrorMessage(error)}`,
            stepId: cause?.step_id,
          });
        });
    }, 250);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
      requestGeneration.current = generation + 1;
    };
  }, [client, ready, selectedWorkflow, workflow, selectedId, requestKey]);

  const filterSteps = useMemo(() => {
    const index = workflow.steps.findIndex(
      (step) => step.step_id === selectedId,
    );
    return workflow.steps
      .slice(0, index + 1)
      .filter((step) =>
        ["filter_rows", "date_range_filter", "date_period_filter"].includes(
          step.key,
        ),
      );
  }, [workflow, selectedId]);
  const filterColumns = useMemo(
    () => [
      ...new Set(
        filterSteps.flatMap((step) => {
          const names: string[] = [];
          function visit(value: unknown) {
            if (!value || typeof value !== "object") return;
            if ("column" in value && typeof value.column === "string")
              names.push(value.column);
            Object.values(value).forEach(visit);
          }
          visit(step.parameters);
          return names;
        }),
      ),
    ],
    [filterSteps],
  );

  function openAction(key: string, columns = selectedColumns, value?: unknown) {
    const step = createActionStep(
      key,
      columns,
      schemas,
      preview?.frame_schema ?? {},
      value,
    );
    beginStep(step, false, columns);
  }

  function beginStep(
    step: StepConfig,
    editing: boolean,
    columns: string[] = [],
  ) {
    const index = workflow.steps.findIndex(
      (item) => item.step_id === step.step_id,
    );
    setDialog({
      step: structuredClone(step),
      editing,
      columns,
      sources: [],
      inputSchema: editing
        ? index === 0
          ? {}
          : preview?.step_id === step.step_id
            ? preview.input_schema
            : {}
        : (preview?.frame_schema ?? {}),
    });
  }

  function openEdit(step: StepConfig) {
    dispatch({ type: "select", id: step.step_id });
    beginStep(step, true);
    setFilterColumn(null);
  }

  function commitSteps(steps: StepConfig[]) {
    dispatch({ type: "commit", snapshot: insertSteps(editor.present, steps) });
    setFilterColumn(null);
  }

  function applyDialog(dialog: StepDialogDraft) {
    if (dialog.editing) {
      const index = workflow.steps.findIndex(
        (step) => step.step_id === dialog.step.step_id,
      );
      const steps = [...workflow.steps];
      steps.splice(index, 1, ...dialog.sources, dialog.step);
      dispatch({
        type: "commit",
        snapshot: {
          workflow: { ...workflow, steps },
          selectedId: dialog.step.step_id,
        },
      });
    } else commitSteps([...dialog.sources, dialog.step]);
    setDialog(null);
  }

  function deleteStep(id: string) {
    const index = workflow.steps.findIndex((step) => step.step_id === id);
    const steps = workflow.steps.filter((step) => step.step_id !== id);
    dispatch({
      type: "commit",
      snapshot: {
        workflow: { ...workflow, steps },
        selectedId:
          selectedId === id
            ? (steps[Math.max(0, index - 1)]?.step_id ?? null)
            : selectedId,
      },
    });
  }

  function moveStep(index: number, direction: number) {
    const steps = [...workflow.steps];
    const target = index + direction;
    if (target < 0 || target >= steps.length) return;
    [steps[index], steps[target]] = [steps[target], steps[index]];
    dispatch({
      type: "commit",
      snapshot: { workflow: { ...workflow, steps }, selectedId },
    });
  }

  async function saveWorkflow(): Promise<boolean> {
    if (!selectedWorkflow || saving) return false;
    const snapshot = structuredClone(workflow);
    setSaving(true);
    try {
      await client.updateWorkflow(selectedWorkflow, snapshot);
      dispatch({ type: "saved", workflow: snapshot });
      notifications.show({
        title: "Workflow saved",
        message: selectedWorkflow,
        color: "ember",
      });
      return true;
    } catch (error) {
      notifications.show({
        title: "Save failed",
        message: getErrorMessage(error),
        color: "red",
      });
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function runWorkflow() {
    if (!selectedWorkflow) return;
    setRunning(true);
    try {
      if (dirty && !(await saveWorkflow())) return;
      await client.runWorkflow(selectedWorkflow);
      setRefresh((value) => value + 1);
      notifications.show({
        title: "Run completed",
        message: selectedWorkflow,
        color: "teal",
      });
    } catch (error) {
      notifications.show({
        title: "Run failed",
        message: getErrorMessage(error),
        color: "red",
      });
    } finally {
      setRunning(false);
    }
  }

  const controlsDisabled = running || saving;

  if (!ready)
    return loadError ? (
      <Alert color="red">{loadError}</Alert>
    ) : (
      <Group>
        <Loader size="sm" />
        <Text>Loading workflow…</Text>
      </Group>
    );

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Group gap="sm">
          <ActionIcon
            aria-label="Back to workflows"
            variant="subtle"
            onClick={() => navigate("/workflows")}
          >
            <IconArrowLeft size={18} />
          </ActionIcon>
          <Box>
            <Group gap="xs">
              <Title order={3}>{workflow.name}</Title>
              {dirty && (
                <Badge color="ember" size="xs">
                  Unsaved
                </Badge>
              )}
            </Group>
            <Text size="xs" c="dimmed">
              {workflow.steps.length} steps ·{" "}
              {selectedStep
                ? `Preview through ${selectedStep.name || selectedStep.key}`
                : "Add a source to begin"}
            </Text>
          </Box>
        </Group>
        <Group gap="xs">
          <Tooltip label="Undo">
            <ActionIcon
              aria-label="Undo"
              variant="default"
              disabled={!editor.past.length || controlsDisabled}
              onClick={() => dispatch({ type: "undo" })}
            >
              <IconArrowBackUp size={17} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Redo">
            <ActionIcon
              aria-label="Redo"
              variant="default"
              disabled={!editor.future.length || controlsDisabled}
              onClick={() => dispatch({ type: "redo" })}
            >
              <IconArrowForwardUp size={17} />
            </ActionIcon>
          </Tooltip>
          <Button
            variant="default"
            leftSection={<IconSchema size={16} />}
            onClick={() => setGraphOpen(true)}
          >
            Graph
          </Button>
          <Button
            variant="default"
            leftSection={<IconDeviceFloppy size={16} />}
            disabled={!dirty || controlsDisabled}
            loading={saving}
            onClick={() => void saveWorkflow()}
          >
            Save
          </Button>
          <Button
            color="ember"
            leftSection={<IconPlayerPlay size={16} />}
            disabled={controlsDisabled || !workflow.steps.length}
            loading={running}
            onClick={() => void runWorkflow()}
          >
            Run workflow
          </Button>
        </Group>
      </Group>
      <Group className="fire-panel" p="sm" gap="xs">
        <Button
          size="xs"
          variant="light"
          leftSection={<IconPlus size={14} />}
          disabled={controlsDisabled}
          onClick={() => setLibraryOpen(true)}
        >
          Add step
        </Button>
        {transformationGroups.map((group) => (
          <Menu key={group.label} withinPortal>
            <Menu.Target>
              <Button
                size="xs"
                variant="default"
                disabled={!preview || outdated || controlsDisabled}
              >
                {group.label}
              </Button>
            </Menu.Target>
            <Menu.Dropdown>
              {group.actions.map(([key, label]) => (
                <Menu.Item key={key} onClick={() => openAction(key)}>
                  {label}…
                </Menu.Item>
              ))}
            </Menu.Dropdown>
          </Menu>
        ))}
        <Menu withinPortal>
          <Menu.Target>
            <Button
              size="xs"
              variant="default"
              disabled={!preview || outdated || controlsDisabled}
            >
              Combine
            </Button>
          </Menu.Target>
          <Menu.Dropdown>
            <Menu.Item onClick={() => openAction("join")}>
              Merge / join…
            </Menu.Item>
            <Menu.Item onClick={() => openAction("concat")}>Append…</Menu.Item>
          </Menu.Dropdown>
        </Menu>
        <Button
          size="xs"
          variant="subtle"
          disabled={!selectedId || controlsDisabled}
          onClick={() => setRefresh((value) => value + 1)}
        >
          Refresh preview
        </Button>
        <Text size="xs" c="dimmed">
          {selectedColumns.length
            ? `${selectedColumns.length} columns selected`
            : "Select columns or open a column menu"}
        </Text>
      </Group>
      <div className="workflow-editor-layout">
        <Box className="fire-panel workflow-table-panel">
          <Group p="sm" justify="space-between">
            <Text size="sm" fw={600}>
              Data preview
            </Text>
            <Group gap="xs">
              {previewBusy && <Loader size="xs" />}
              {outdated && preview && (
                <Badge color="yellow" size="xs">
                  Outdated preview
                </Badge>
              )}
              <Text size="xs" c="dimmed">
                {!outdated && preview
                  ? preview.truncated
                    ? `Showing up to ${preview.data.length} rows`
                    : `${preview.data.length} rows`
                  : ""}
              </Text>
            </Group>
          </Group>
          {currentError && (
            <Alert color="red" m="sm" title="Preview failed">
              {currentError.message}
              {workflow.steps.some(
                (step) => step.step_id === currentError.stepId,
              ) && (
                <Button
                  size="xs"
                  variant="subtle"
                  onClick={() => {
                    const step = workflow.steps.find(
                      (item) => item.step_id === currentError.stepId,
                    );
                    if (step) openEdit(step);
                  }}
                >
                  Edit affected step
                </Button>
              )}
            </Alert>
          )}
          {!selectedId ? (
            <Stack p="xl" align="center">
              <Text c="dimmed">Start by adding a data source.</Text>
              <Button variant="light" onClick={() => setLibraryOpen(true)}>
                Add source
              </Button>
            </Stack>
          ) : preview ? (
            <DataTable
              data={preview.data}
              schema={preview.frame_schema}
              columnOrder={preview.columns}
              selectedColumns={selectedColumns}
              onSelectColumns={setSelectedColumns}
              onAction={openAction}
              onFilters={setFilterColumn}
              filterColumns={filterColumns}
              disabled={outdated || controlsDisabled}
            />
          ) : (
            !currentError && (
              <Text p="xl" c="dimmed">
                Preparing preview…
              </Text>
            )
          )}
        </Box>
        <Stack className="fire-panel workflow-applied-steps" p="sm" gap="xs">
          <Text size="xs" tt="uppercase" fw={700} c="ember.4">
            Applied steps
          </Text>
          <Text size="xs" c="dimmed">
            New actions are inserted after the selected step. Later steps are
            evaluated when selected.
          </Text>
          {workflow.steps.map((step, index) => (
            <Box
              key={step.step_id}
              className={`workflow-applied-step ${step.step_id === selectedId ? "is-selected" : ""}`}
            >
              <Group gap={4} wrap="nowrap">
                <UnstyledButton
                  className="workflow-step-select"
                  disabled={controlsDisabled}
                  onClick={() => {
                    dispatch({ type: "select", id: step.step_id });
                    setFilterColumn(null);
                  }}
                >
                  <Text size="xs" c="dimmed">
                    {index + 1}. {step.key}
                  </Text>
                  <Text size="sm" fw={step.step_id === selectedId ? 600 : 400}>
                    {stepSummary(step)}
                  </Text>
                </UnstyledButton>
                <ActionIcon
                  size="sm"
                  variant="subtle"
                  disabled={controlsDisabled}
                  aria-label={`Edit ${step.name || step.key}`}
                  onClick={() => openEdit(step)}
                >
                  <IconEdit size={14} />
                </ActionIcon>
              </Group>
              <Group gap={4} justify="end">
                <ActionIcon
                  size="xs"
                  variant="subtle"
                  aria-label={`Move step ${index + 1} up`}
                  disabled={index === 0 || controlsDisabled}
                  onClick={() => moveStep(index, -1)}
                >
                  <IconArrowUp size={12} />
                </ActionIcon>
                <ActionIcon
                  size="xs"
                  variant="subtle"
                  aria-label={`Move step ${index + 1} down`}
                  disabled={
                    index === workflow.steps.length - 1 || controlsDisabled
                  }
                  onClick={() => moveStep(index, 1)}
                >
                  <IconArrowDown size={12} />
                </ActionIcon>
                <ActionIcon
                  size="xs"
                  color="red"
                  variant="subtle"
                  aria-label={`Delete step ${index + 1}`}
                  disabled={controlsDisabled}
                  onClick={() => deleteStep(step.step_id)}
                >
                  <IconTrash size={12} />
                </ActionIcon>
              </Group>
            </Box>
          ))}
        </Stack>
      </div>
      <Drawer
        opened={libraryOpen}
        onClose={() => setLibraryOpen(false)}
        title="Add step"
        position="left"
        size="sm"
      >
        <Box h="75vh">
          <StepLibrary
            onSelect={(step) => {
              setLibraryOpen(false);
              beginStep(step, false, selectedColumns);
            }}
          />
        </Box>
      </Drawer>
      {dialog && (
        <StepSettingsDrawer
          initial={dialog}
          workflow={workflow}
          workflowName={selectedWorkflow!}
          selectedId={selectedId}
          onClose={() => setDialog(null)}
          onApply={applyDialog}
        />
      )}
      <Modal
        opened={graphOpen}
        onClose={() => setGraphOpen(false)}
        title="Workflow graph"
        size="90%"
      >
        <Box h="70vh">
          <WorkflowGraph
            steps={workflow.steps}
            selectedStepId={selectedId}
            onSelect={(step) => dispatch({ type: "select", id: step.step_id })}
          />
        </Box>
        {selectedStep && (
          <Group justify="end" mt="sm">
            <Button
              variant="light"
              onClick={() => {
                setGraphOpen(false);
                openEdit(selectedStep);
              }}
            >
              Edit selected step
            </Button>
          </Group>
        )}
      </Modal>
      <Modal
        opened={filterColumn !== null}
        onClose={() => setFilterColumn(null)}
        title={`Applied filters: ${filterColumn ?? ""}`}
      >
        <Stack>
          {filterSteps
            .filter((step) =>
              JSON.stringify(step.parameters).includes(
                JSON.stringify(filterColumn),
              ),
            )
            .map((step) => (
              <Button
                variant="default"
                key={step.step_id}
                onClick={() => openEdit(step)}
              >
                {stepSummary(step)}
              </Button>
            ))}
          <Text size="xs" c="dimmed">
            Edit or delete individual steps to change their filtering behavior.
          </Text>
        </Stack>
      </Modal>
      <Modal
        opened={blocker.state === "blocked"}
        onClose={() => blocker.state === "blocked" && blocker.reset()}
        title="Discard unsaved changes?"
      >
        <Text size="sm">
          Your draft or open transformation has unsaved changes.
        </Text>
        <Group justify="end" mt="md">
          <Button
            variant="default"
            onClick={() => blocker.state === "blocked" && blocker.reset()}
          >
            Keep editing
          </Button>
          <Button
            color="red"
            onClick={() => blocker.state === "blocked" && blocker.proceed()}
          >
            Discard and leave
          </Button>
        </Group>
      </Modal>
    </Stack>
  );
}

import {
  useContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";
import {
  Badge,
  Box,
  Button,
  Group,
  LoadingOverlay,
  Skeleton,
  Stack,
  Text,
  ThemeIcon,
  Title,
  ActionIcon,
  Tooltip,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  IconArrowLeft,
  IconDeviceFloppy,
  IconFlame,
  IconPlayerPlay,
  IconTable,
} from "@tabler/icons-react";

import type {
  StepConfig,
  WorkflowFullConfig,
} from "@/types/workflows";

import { ClientContext } from "@/context/api_context";

import { WorkflowGraph } from "@/components/workflow_graph";
import { StepEdit } from "@/components/step_edit";
import { PreviewTable } from "@/components/preview_table";
import { StepLibrary } from "@/components/step_library";
import { ErrorTraceback } from "@/components/error_traceback";
import {
  setValueAtPath,
  type ParameterPath,
} from "@/components/step_editor/model";
import { getErrorMessage, getRunErrorBody, formatNumber } from "@/lib/format";

type WorkflowDetailsProps = {
  selectedWorkflow: string | null;
};

type PreviewRow = Record<string, unknown>;

export function WorkflowDetails({
  selectedWorkflow,
}: WorkflowDetailsProps) {
  const client = useContext(ClientContext);
  const navigate = useNavigate();

  const [workflowDetails, setWorkflowDetails] =
    useState<WorkflowFullConfig | null>(null);

  const [selectedStepId, setSelectedStepId] =
    useState<string | null>(null);

  const [preview, setPreview] =
    useState<PreviewRow[] | null>(null);

  const [previewSchema, setPreviewSchema] =
    useState<Record<string, unknown>>({});

  const [running, setRunning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [lastRowCount, setLastRowCount] = useState<number | null>(null);

  const selectedStep = useMemo(() => {
    if (
      workflowDetails === null ||
      selectedStepId === null
    ) {
      return null;
    }

    return (
      workflowDetails.content.steps.find(
        (step) => step.step_id === selectedStepId,
      ) ?? null
    );
  }, [workflowDetails, selectedStepId]);

  async function runWorkflow(workflowName: string) {
    setRunning(true);

    try {
      const response =
        await client.runWorkflow(workflowName);

      setPreview(response.preview ?? null);
      setLastRowCount(response.row_count ?? response.preview?.length ?? null);
      setPreviewSchema(
        response.preview?.[0] === undefined
          ? {}
          : Object.fromEntries(
              Object.keys(response.preview[0]).map(
                (column) => [column, "unknown"],
              ),
            ),
      );

      notifications.show({
        title: "Run completed",
        message: `"${workflowName}" finished successfully.`,
        color: "teal",
      });
    } catch (error) {
      console.error("Failed to run workflow:", error);
      notifications.show({
        title: "Run failed",
        message: getErrorMessage(error),
        color: "red",
      });
    } finally {
      setRunning(false);
    }
  }

  async function saveWorkflow() {
    if (
      selectedWorkflow === null ||
      workflowDetails === null ||
      saving
    ) {
      return;
    }

    setSaving(true);

    try {
      await client.updateWorkflow(
        selectedWorkflow,
        workflowDetails.content,
      );

      setIsDirty(false);

      notifications.show({
        title: "Workflow saved",
        message: `"${selectedWorkflow}" was updated.`,
        color: "ember",
      });
    } catch (error) {
      console.error("Failed to save workflow:", error);
      notifications.show({
        title: "Save failed",
        message: getErrorMessage(error),
        color: "red",
      });
    } finally {
      setSaving(false);
    }
  }

  const getCachedPreview = useCallback(async (
    workflowName: string,
  ) => {
    try {
      const response =
        await client.getCachedPreview(workflowName);

      setPreview(response.data);
      setLastRowCount(response.row_count ?? response.data.length);
      setPreviewSchema(response.frame_schema ?? {});
    } catch (error) {
      console.debug(
        "No cached preview available.",
        error,
      );

      setPreview(null);
      setPreviewSchema({});
      setLastRowCount(null);
    }
  }, [client]);

  const loadWorkflowDetails = useCallback(async (
    workflowName: string,
  ) => {
    try {
      const details =
        await client.getWorkflow(workflowName);

      setWorkflowDetails(details);
      setSelectedStepId(null);
      setIsDirty(false);

      setPreviewLoading(true);
      await getCachedPreview(workflowName);
      setPreviewLoading(false);
    } catch (error) {
      console.error(
        "Failed to load workflow details:",
        error,
      );

      notifications.show({
        title: "Could not load workflow",
        message: getErrorMessage(error),
        color: "red",
      });

      setWorkflowDetails(null);
      setSelectedStepId(null);
      setPreview(null);
      setPreviewSchema({});
      setIsDirty(false);
    }
  }, [client, getCachedPreview]);

  function addStep(stepTemplate: StepConfig) {
    const newStep: StepConfig = {
      ...stepTemplate,
      step_id: crypto.randomUUID(),
      parameters: structuredClone(
        stepTemplate.parameters ?? {},
      ),
    };

    setWorkflowDetails((currentWorkflow) => {
      if (currentWorkflow === null) {
        return null;
      }

      return {
        ...currentWorkflow,
        content: {
          ...currentWorkflow.content,
          steps: [
            ...currentWorkflow.content.steps,
            newStep,
          ],
        },
      };
    });

    setSelectedStepId(newStep.step_id);
    setIsDirty(true);
  }

  function deleteStep(stepId: string) {
    setWorkflowDetails((currentWorkflow) => {
      if (currentWorkflow === null) {
        return null;
      }

      return {
        ...currentWorkflow,
        content: {
          ...currentWorkflow.content,
          steps: currentWorkflow.content.steps.filter(
            (step) => step.step_id !== stepId,
          ),
        },
      };
    });

    setSelectedStepId((currentSelectedStepId) =>
      currentSelectedStepId === stepId
        ? null
        : currentSelectedStepId,
    );

    setIsDirty(true);
  }

  function updateStepParameter(
    stepId: string,
    path: ParameterPath,
    value: unknown,
  ) {
    setWorkflowDetails((currentWorkflow) => {
      if (currentWorkflow === null) {
        return null;
      }

      return {
        ...currentWorkflow,
        content: {
          ...currentWorkflow.content,
          steps: currentWorkflow.content.steps.map(
            (step) => {
              if (step.step_id !== stepId) {
                return step;
              }

              return {
                ...step,
                parameters: setValueAtPath(
                  step.parameters,
                  path,
                  value,
                ),
              };
            },
          ),
        },
      };
    });

    setIsDirty(true);
  }

  useEffect(() => {
    if (selectedWorkflow === null) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      void loadWorkflowDetails(selectedWorkflow);
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [selectedWorkflow, loadWorkflowDetails]);

  if (selectedWorkflow === null || workflowDetails === null) {
    return (
      <Stack gap="md">
        <Skeleton height={44} radius="md" />
        <Skeleton height={420} radius="lg" />
      </Stack>
    );
  }

  const stepCount = workflowDetails.content.steps.length;

  return (
    <Stack gap="md" h="100%">
      <Group justify="space-between" align="center">
        <Group gap={10}>
          <Tooltip label="Back to workflows">
            <ActionIcon variant="subtle" color="gray" onClick={() => navigate("/workflows")}>
              <IconArrowLeft size={18} />
            </ActionIcon>
          </Tooltip>
          <ThemeIcon variant="gradient" gradient={{ from: "#7c2d0f", to: "#f2600a", deg: 135 }} size={34} radius="md">
            <IconFlame size={18} />
          </ThemeIcon>
          <Box>
            <Group gap={8} align="baseline">
              <Title order={3}>{workflowDetails.name}</Title>
              {isDirty && (
                <Badge size="xs" color="ember" variant="light">
                  Unsaved
                </Badge>
              )}
            </Group>
            <Text size="xs" c="dimmed">
              {stepCount} {stepCount === 1 ? "step" : "steps"}
            </Text>
          </Box>
        </Group>

        <Group gap="sm">
          <Button
            variant="default"
            leftSection={<IconDeviceFloppy size={16} />}
            disabled={saving || !isDirty}
            loading={saving}
            onClick={() => void saveWorkflow()}
          >
            {saving ? "Saving…" : "Save"}
          </Button>

          <Button
            variant="gradient"
            gradient={{ from: "#b23e08", to: "#ff9d3d", deg: 120 }}
            leftSection={<IconPlayerPlay size={16} />}
            disabled={running}
            loading={running}
            onClick={() => void runWorkflow(selectedWorkflow)}
          >
            {running ? "Running…" : "Run workflow"}
          </Button>
        </Group>
      </Group>

      <Group
        align="stretch"
        gap="md"
        wrap="nowrap"
        style={{ height: "58vh", minHeight: 460 }}
      >
        <StepLibrary onSelect={addStep} />

        <WorkflowGraph
          steps={workflowDetails.content.steps}
          selectedStepId={selectedStepId}
          onSelect={(step) =>
            setSelectedStepId(step.step_id)
          }
        />

        {selectedStep !== null && (
          <StepEdit
            step={selectedStep}
            availableColumns={Object.keys(previewSchema)}
            onDelete={deleteStep}
            onParameterChange={
              updateStepParameter
            }
          />
        )}
      </Group>

      <Box className="fire-panel" p="md" style={{ position: "relative", minHeight: 160 }}>
        <Group justify="space-between" mb="sm">
          <Group gap={8}>
            <IconTable size={16} color="#f2600a" />
            <Text fw={700} size="sm" tt="uppercase" c="ember.4" style={{ letterSpacing: "0.05em" }}>
              Data preview
            </Text>
          </Group>
          {lastRowCount !== null && (
            <Text size="xs" c="dimmed">
              {formatNumber(lastRowCount)} rows
            </Text>
          )}
        </Group>

        <LoadingOverlay
          visible={running || previewLoading}
          zIndex={5}
          overlayProps={{ radius: "md", blur: 2, backgroundOpacity: 0.35 }}
          loaderProps={{ color: "ember", type: "dots" }}
        />

        {preview === null ? (
          <Text size="sm" c="dimmed" py="lg" ta="center">
            Run the workflow to see a data preview.
          </Text>
        ) : (
          <PreviewTable data={preview} />
        )}
      </Box>
    </Stack>
  );
}

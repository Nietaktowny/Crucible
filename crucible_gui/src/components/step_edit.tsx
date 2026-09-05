import {
  useCallback,
  useContext,
  useMemo,
} from "react";
import { Box, Button, Group, ScrollArea, Stack, Text, ThemeIcon, Title } from "@mantine/core";
import { IconFlame, IconTrash } from "@tabler/icons-react";

import type { StepConfig } from "@/types/workflows";
import {
  ClientContext,
  SchemaContext,
} from "@/context/api_context";

import type { ParameterPath } from "./step_editor/model";
import { StepForm } from "./step_editor/step_form";

type StepEditProps = {
  step: StepConfig;
  availableColumns: string[];
  leftColumns?: string[];
  rightColumns?: string[];
  onDelete: (stepId: string) => void;
  onParameterChange: (
    stepId: string,
    path: ParameterPath,
    value: unknown,
  ) => void;
};

export function StepEdit({
  step,
  availableColumns,
  leftColumns = availableColumns,
  rightColumns = availableColumns,
  onDelete,
  onParameterChange,
}: StepEditProps) {
  const schemas = useContext(SchemaContext);
  const client = useContext(ClientContext);
  const schema = schemas.find(
    (candidate) => candidate.key === step.key,
  );

  const loadSheets = useCallback(
    (path: string) => client.getExcelSheets(path),
    [client],
  );

  const context = useMemo(
    () => ({
      stepKey: step.key,
      parameters: step.parameters ?? {},
      inputColumns: availableColumns,
      leftColumns,
      rightColumns,
      loadSheets,
    }),
    [
      step.key,
      step.parameters,
      availableColumns,
      leftColumns,
      rightColumns,
      loadSheets,
    ],
  );

  if (schema === undefined) {
    return (
      <Box className="fire-panel" p="md" style={{ width: 340, flex: "0 0 340px" }}>
        <Text c="red">
          The schema for step “{step.key}” is not available.
        </Text>
      </Box>
    );
  }

  return (
    <Box
      className="fire-panel"
      p="md"
      style={{ width: 340, flex: "0 0 340px", display: "flex", flexDirection: "column", height: "100%" }}
    >
      <Group gap={10} mb="sm" wrap="nowrap">
        <ThemeIcon variant="gradient" gradient={{ from: "#7c2d0f", to: "#f2600a", deg: 135 }} size={34} radius="md">
          <IconFlame size={18} />
        </ThemeIcon>
        <Box style={{ minWidth: 0 }}>
          <Text size="10px" tt="uppercase" c="dimmed" fw={700} style={{ letterSpacing: "0.08em" }}>
            Step editor
          </Text>
          <Title order={5} style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {step.name}
          </Title>
        </Box>
      </Group>

      {(step.description || schema.default_description) && (
        <Text size="xs" c="dimmed" mb="sm">
          {step.description || schema.default_description}
        </Text>
      )}

      <ScrollArea style={{ flex: 1 }} offsetScrollbars type="auto">
        <Stack gap="md" pr={4} pb="md">
          <StepForm
            schema={schema}
            context={context}
            onChange={(path, value) =>
              onParameterChange(step.step_id, path, value)
            }
          />
        </Stack>
      </ScrollArea>

      <Button
        type="button"
        color="red"
        variant="light"
        leftSection={<IconTrash size={15} />}
        onClick={() => onDelete(step.step_id)}
        mt="sm"
      >
        Delete step
      </Button>
    </Box>
  );
}

import {
  ActionIcon,
  Button,
  Group,
  Paper,
  Select,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";

import type { StepPropertySchema } from "@/types/step_schema";

import { FieldEditor } from "./field_editor";
import { LiteralValueEditor } from "./literal_value_editor";
import type { StepEditorContext } from "./model";

type MultiFieldChange = (
  key: string,
  value: unknown,
) => void;

function toStringList(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter(
      (item): item is string => typeof item === "string",
    );
  }

  return typeof value === "string" && value
    ? [value]
    : [];
}

function JoinColumnInput({
  value,
  columns,
  label,
  onChange,
}: {
  value: string;
  columns: string[];
  label: string;
  onChange: (value: string) => void;
}) {
  if (columns.length === 0) {
    return (
      <TextInput
        label={label}
        value={value}
        placeholder="Column name"
        onChange={(event) =>
          onChange(event.currentTarget.value)
        }
      />
    );
  }

  return (
    <Select
      label={label}
      searchable
      value={value || null}
      data={Array.from(
        new Set([...columns, ...(value ? [value] : [])]),
      )}
      onChange={(column) => onChange(column ?? "")}
    />
  );
}

export function JoinKeysEditor({
  context,
  onChange,
}: {
  context: StepEditorContext;
  onChange: MultiFieldChange;
}) {
  const leftKeys = toStringList(context.parameters.left_on);
  const rightKeys = toStringList(context.parameters.right_on);
  const pairCount = Math.max(
    leftKeys.length,
    rightKeys.length,
  );
  const pairs = Array.from({ length: pairCount }, (_, index) => ({
    left: leftKeys[index] ?? "",
    right: rightKeys[index] ?? "",
  }));

  const updatePairs = (
    nextPairs: Array<{ left: string; right: string }>,
  ) => {
    onChange(
      "left_on",
      nextPairs.map((pair) => pair.left),
    );
    onChange(
      "right_on",
      nextPairs.map((pair) => pair.right),
    );
  };

  return (
    <div className="step-editor-field">
      <Text size="sm" fw={600}>
        Join key pairs *
      </Text>
      <Text size="xs" c="dimmed">
        Keys are paired by row, so the left and right lists cannot drift.
      </Text>

      <Stack gap="xs">
        {pairs.map((pair, index) => (
          <Paper key={index} withBorder p="xs">
            <Group align="flex-end" wrap="nowrap">
              <div className="step-editor-grow">
                <JoinColumnInput
                  label="Left column"
                  value={pair.left}
                  columns={context.leftColumns}
                  onChange={(left) => {
                    const next = [...pairs];
                    next[index] = { ...pair, left };
                    updatePairs(next);
                  }}
                />
              </div>
              <div className="step-editor-grow">
                <JoinColumnInput
                  label="Right column"
                  value={pair.right}
                  columns={context.rightColumns}
                  onChange={(right) => {
                    const next = [...pairs];
                    next[index] = { ...pair, right };
                    updatePairs(next);
                  }}
                />
              </div>
              <ActionIcon
                variant="subtle"
                color="red"
                aria-label="Remove join key pair"
                onClick={() =>
                  updatePairs(
                    pairs.filter(
                      (_, itemIndex) => itemIndex !== index,
                    ),
                  )
                }
              >
                ×
              </ActionIcon>
            </Group>
          </Paper>
        ))}

        <Button
          size="xs"
          variant="default"
          onClick={() =>
            updatePairs([...pairs, { left: "", right: "" }])
          }
        >
          Add key pair
        </Button>
      </Stack>
    </div>
  );
}

export function ReplacementEditor({
  fields,
  context,
  onChange,
}: {
  fields: Record<string, StepPropertySchema>;
  context: StepEditorContext;
  onChange: MultiFieldChange;
}) {
  const mappingValue = context.parameters.mapping;
  const mode =
    mappingValue !== undefined && mappingValue !== null
      ? "mapping"
      : "pair";

  return (
    <div className="step-editor-field">
      <Text size="sm" fw={600}>
        Replacement mode *
      </Text>
      <Stack gap="xs">
        <Select
          value={mode}
          allowDeselect={false}
          data={[
            { value: "pair", label: "One old/new pair" },
            { value: "mapping", label: "Multiple replacements" },
          ]}
          onChange={(nextMode) => {
            if (nextMode === "mapping") {
              onChange("old", undefined);
              onChange("new", undefined);
              onChange("mapping", {});
            } else if (nextMode === "pair") {
              onChange("mapping", undefined);
              onChange("old", "");
              onChange("new", "");
            }
          }}
        />

        {mode === "pair" ? (
          <Group align="flex-start" grow>
            <LiteralValueEditor
              label="Old value"
              value={context.parameters.old}
              onChange={(value) => onChange("old", value)}
            />
            <LiteralValueEditor
              label="New value"
              value={context.parameters.new}
              onChange={(value) => onChange("new", value)}
            />
          </Group>
        ) : fields.mapping !== undefined ? (
          <FieldEditor
            field={fields.mapping}
            value={mappingValue}
            context={context}
            onChange={(value) => onChange("mapping", value)}
          />
        ) : null}
      </Stack>
    </div>
  );
}

export function DateEndpointEditor({
  label,
  columnKey,
  valueKey,
  context,
  onChange,
}: {
  label: string;
  columnKey: "start_column" | "end_column";
  valueKey: "start_value" | "end_value";
  context: StepEditorContext;
  onChange: MultiFieldChange;
}) {
  const column = context.parameters[columnKey];
  const literal = context.parameters[valueKey];
  const mode = literal !== undefined && literal !== null
    ? "value"
    : "column";
  const columnValue = typeof column === "string" ? column : "";
  const literalValue = typeof literal === "string" ? literal : "";

  return (
    <div className="step-editor-field">
      <Text size="sm" fw={600}>
        {label} *
      </Text>
      <Stack gap="xs">
        <Select
          value={mode}
          allowDeselect={false}
          data={[
            { value: "column", label: "Column" },
            { value: "value", label: "Fixed date/time" },
          ]}
          onChange={(nextMode) => {
            if (nextMode === "value") {
              onChange(columnKey, undefined);
              onChange(valueKey, "");
            } else if (nextMode === "column") {
              onChange(valueKey, undefined);
              onChange(columnKey, "");
            }
          }}
        />

        {mode === "column" ? (
          <JoinColumnInput
            label={`${label} column`}
            value={columnValue}
            columns={context.inputColumns}
            onChange={(value) => onChange(columnKey, value)}
          />
        ) : (
          <TextInput
            type="datetime-local"
            value={literalValue}
            onChange={(event) =>
              onChange(valueKey, event.currentTarget.value)
            }
          />
        )}
      </Stack>
    </div>
  );
}

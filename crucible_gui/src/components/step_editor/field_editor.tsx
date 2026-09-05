import { useEffect, useMemo, useState } from "react";
import {
  ActionIcon,
  Button,
  Checkbox,
  Group,
  Loader,
  MultiSelect,
  NumberInput,
  Paper,
  Select,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";

import type { StepPropertySchema } from "@/types/step_schema";

import { ConditionEditor } from "./condition_editor";
import { ExpressionEditor } from "./expression_editor";
import { LiteralValueEditor } from "./literal_value_editor";
import {
  getInitialValue,
  isEmptyValue,
  type StepEditorContext,
} from "./model";

type FieldEditorProps = {
  field: StepPropertySchema;
  value: unknown;
  context: StepEditorContext;
  onChange: (value: unknown) => void;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null &&
    typeof value === "object" &&
    !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter(
        (item): item is string => typeof item === "string",
      )
    : [];
}

function getColumns(
  field: StepPropertySchema,
  context: StepEditorContext,
): string[] {
  switch (field.source) {
    case "left-schema":
      return context.leftColumns;
    case "right-schema":
      return context.rightColumns;
    default:
      return context.inputColumns;
  }
}

function mergeCurrentOptions(
  options: string[],
  current: string[],
): string[] {
  return Array.from(new Set([...options, ...current]));
}

function FieldFrame({
  field,
  value,
  children,
}: {
  field: StepPropertySchema;
  value: unknown;
  children: React.ReactNode;
}) {
  const missing = field.required && isEmptyValue(value);

  return (
    <div className="step-editor-field">
      <Text size="sm" fw={600}>
        {field.title}
        {field.required ? " *" : ""}
      </Text>

      {field.description && (
        <Text size="xs" c="dimmed">
          {field.description}
        </Text>
      )}

      {children}

      {field.help && (
        <Text size="xs" c="dimmed">
          {field.help}
        </Text>
      )}

      {missing && (
        <Text size="xs" c="red">
          This field is required.
        </Text>
      )}
    </div>
  );
}

function ColumnSelectEditor({
  field,
  value,
  context,
  onChange,
}: FieldEditorProps) {
  const columns = getColumns(field, context);
  const current = typeof value === "string" ? value : "";

  if (columns.length === 0) {
    return (
      <TextInput
        value={current}
        placeholder="Enter a column name"
        description="No input schema is available yet."
        onChange={(event) =>
          onChange(event.currentTarget.value || undefined)
        }
      />
    );
  }

  return (
    <Select
      searchable
      clearable={!field.required}
      placeholder="Select a column"
      value={current || null}
      data={mergeCurrentOptions(columns, current ? [current] : [])}
      onChange={(column) => onChange(column ?? undefined)}
    />
  );
}

function ColumnMultiSelectEditor({
  field,
  value,
  context,
  onChange,
}: FieldEditorProps) {
  const columns = getColumns(field, context);
  const selected = asStringArray(value);

  if (columns.length === 0) {
    return (
      <StringListEditor
        field={field.items ?? {
          ...field,
          key: `${field.key}[]`,
          title: "Column",
          editor: "text",
          required: true,
        }}
        value={selected}
        context={context}
        onChange={onChange}
        addLabel="Add column"
      />
    );
  }

  return (
    <MultiSelect
      searchable
      clearable
      placeholder="Select columns"
      data={mergeCurrentOptions(columns, selected)}
      value={selected}
      onChange={onChange}
    />
  );
}

function SheetSelectEditor({
  value,
  context,
  onChange,
}: FieldEditorProps) {
  const path = typeof context.parameters.path === "string"
    ? context.parameters.path
    : "";
  const current = typeof value === "string" ? value : "";

  if (!path) {
    return (
      <Select
        disabled
        placeholder="Choose a file first"
        value={current || null}
        data={current ? [current] : []}
      />
    );
  }

  return (
    <LoadedSheetSelect
      key={path}
      path={path}
      value={current}
      loadSheets={context.loadSheets}
      onChange={onChange}
    />
  );
}

function LoadedSheetSelect({
  path,
  value,
  loadSheets,
  onChange,
}: {
  path: string;
  value: string;
  loadSheets: (path: string) => Promise<string[]>;
  onChange: (value: unknown) => void;
}) {
  const [sheets, setSheets] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void loadSheets(path)
      .then((availableSheets) => {
        if (!cancelled) {
          setSheets(availableSheets);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSheets([]);
          setError("Sheets could not be loaded for this path.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [path, loadSheets]);

  return (
    <Stack gap="xs">
      <Select
        searchable
        clearable
        disabled={loading}
        placeholder="Select a sheet"
        value={value || null}
        data={mergeCurrentOptions(
          sheets,
          value ? [value] : [],
        )}
        rightSection={loading ? <Loader size="xs" /> : undefined}
        onChange={(sheet) => onChange(sheet ?? null)}
      />
      {error && (
        <Text size="xs" c="red">
          {error}
        </Text>
      )}
    </Stack>
  );
}

function OrderedColumnListEditor({
  value,
  context,
  onChange,
}: FieldEditorProps) {
  const selected = asStringArray(value);
  const available = context.inputColumns.filter(
    (column) => !selected.includes(column),
  );

  const move = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= selected.length) {
      return;
    }

    const next = [...selected];
    [next[index], next[target]] = [next[target], next[index]];
    onChange(next);
  };

  return (
    <Stack gap="xs">
      {selected.map((column, index) => (
        <Paper key={`${column}-${index}`} withBorder p="xs">
          <Group wrap="nowrap">
            <div className="step-editor-grow">
              {context.inputColumns.length === 0 ? (
                <TextInput
                  value={column}
                  placeholder="Column name"
                  onChange={(event) => {
                    const next = [...selected];
                    next[index] = event.currentTarget.value;
                    onChange(next);
                  }}
                />
              ) : (
                <Text size="sm">
                  {column}
                </Text>
              )}
            </div>
            <ActionIcon
              variant="subtle"
              aria-label="Move up"
              disabled={index === 0}
              onClick={() => move(index, -1)}
            >
              ↑
            </ActionIcon>
            <ActionIcon
              variant="subtle"
              aria-label="Move down"
              disabled={index === selected.length - 1}
              onClick={() => move(index, 1)}
            >
              ↓
            </ActionIcon>
            <ActionIcon
              variant="subtle"
              color="red"
              aria-label="Remove column"
              onClick={() =>
                onChange(
                  selected.filter((_, itemIndex) => itemIndex !== index),
                )
              }
            >
              ×
            </ActionIcon>
          </Group>
        </Paper>
      ))}

      {available.length > 0 ? (
        <Select
          searchable
          placeholder="Add a column"
          value={null}
          data={available}
          onChange={(column) => {
            if (column !== null) {
              onChange([...selected, column]);
            }
          }}
        />
      ) : context.inputColumns.length === 0 ? (
        <Button
          size="xs"
          variant="default"
          onClick={() => onChange([...selected, ""])}
        >
          Add column name
        </Button>
      ) : null}

    </Stack>
  );
}

function StringListEditor({
  field,
  value,
  context,
  onChange,
  addLabel = "Add item",
}: FieldEditorProps & { addLabel?: string }) {
  const items = asArray(value);

  return (
    <Stack gap="xs">
      {items.map((item, index) => (
        <Group key={index} align="flex-start" wrap="nowrap">
          <div className="step-editor-grow">
            <FieldEditorControl
              field={{
                ...field,
                title: `Item ${index + 1}`,
                required: true,
              }}
              value={item}
              context={context}
              onChange={(nextItem) => {
                const next = [...items];
                next[index] = nextItem;
                onChange(next);
              }}
            />
          </div>
          <ActionIcon
            variant="subtle"
            color="red"
            aria-label="Remove item"
            onClick={() =>
              onChange(
                items.filter((_, itemIndex) => itemIndex !== index),
              )
            }
          >
            ×
          </ActionIcon>
        </Group>
      ))}
      <Button
        size="xs"
        variant="default"
        onClick={() =>
          onChange([...items, getInitialValue(field)])
        }
      >
        {addLabel}
      </Button>
    </Stack>
  );
}

function ObjectListEditor({
  field,
  value,
  context,
  onChange,
}: FieldEditorProps) {
  const items = asArray(value).map(asRecord);
  const itemSchema = field.items;

  if (itemSchema === null) {
    return (
      <StringListEditor
        field={field}
        value={value}
        context={context}
        onChange={onChange}
      />
    );
  }

  return (
    <Stack gap="xs">
      {items.map((item, index) => (
        <Paper key={index} withBorder p="sm">
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="sm" fw={600}>
                Item {index + 1}
              </Text>
              <Group gap={4}>
                <ActionIcon
                  variant="subtle"
                  aria-label="Move item up"
                  disabled={index === 0}
                  onClick={() => {
                    const next = [...items];
                    [next[index - 1], next[index]] = [
                      next[index],
                      next[index - 1],
                    ];
                    onChange(next);
                  }}
                >
                  ↑
                </ActionIcon>
                <ActionIcon
                  variant="subtle"
                  aria-label="Move item down"
                  disabled={index === items.length - 1}
                  onClick={() => {
                    const next = [...items];
                    [next[index], next[index + 1]] = [
                      next[index + 1],
                      next[index],
                    ];
                    onChange(next);
                  }}
                >
                  ↓
                </ActionIcon>
                <ActionIcon
                  variant="subtle"
                  color="red"
                  aria-label="Remove item"
                  onClick={() =>
                    onChange(
                      items.filter(
                        (_, itemIndex) => itemIndex !== index,
                      ),
                    )
                  }
                >
                  ×
                </ActionIcon>
              </Group>
            </Group>

            {itemSchema.properties.map((property) => (
              <FieldEditor
                key={property.key}
                field={property}
                value={item[property.key]}
                context={context}
                onChange={(nextValue) => {
                  const next = [...items];
                  next[index] = {
                    ...item,
                    [property.key]: nextValue,
                  };
                  onChange(next);
                }}
              />
            ))}
          </Stack>
        </Paper>
      ))}

      <Button
        size="xs"
        variant="default"
        onClick={() => {
          const initial = Object.fromEntries(
            itemSchema.properties
              .filter((property) => property.hasDefault)
              .map((property) => [
                property.key,
                getInitialValue(property),
              ]),
          );
          onChange([...items, initial]);
        }}
      >
        Add item
      </Button>
    </Stack>
  );
}

function MappingKeyEditor({
  value,
  context,
  onChange,
}: {
  value: string;
  context: StepEditorContext;
  onChange: (value: string) => void;
}) {
  const usesInputColumns = [
    "rename_columns",
    "change_column_type",
  ].includes(context.stepKey);

  if (usesInputColumns && context.inputColumns.length > 0) {
    return (
      <Select
        searchable
        placeholder="Column"
        value={value || null}
        data={mergeCurrentOptions(
          context.inputColumns,
          value ? [value] : [],
        )}
        onChange={(key) => onChange(key ?? "")}
      />
    );
  }

  return (
    <TextInput
      placeholder={usesInputColumns ? "Column name" : "Key"}
      value={value}
      onChange={(event) => onChange(event.currentTarget.value)}
    />
  );
}

function MappingEditor({
  field,
  value,
  context,
  onChange,
}: FieldEditorProps) {
  const entries = Object.entries(asRecord(value));
  const valueSchema = field.mapping?.value ?? {
    ...field,
    key: "$value",
    title: "Value",
    editor: "value-editor" as const,
    required: true,
  };

  const updateEntries = (nextEntries: Array<[string, unknown]>) => {
    onChange(Object.fromEntries(nextEntries));
  };

  return (
    <Stack gap="xs">
      {entries.map(([key, entryValue], index) => (
        <Paper key={`${key}-${index}`} withBorder p="xs">
          <Group align="flex-start" wrap="nowrap">
            <div className="step-editor-mapping-key">
              <MappingKeyEditor
                value={key}
                context={context}
                onChange={(nextKey) => {
                  const next = [...entries];
                  next[index] = [nextKey, entryValue];
                  updateEntries(next);
                }}
              />
            </div>

            <div className="step-editor-grow">
              <FieldEditorControl
                field={valueSchema}
                value={entryValue}
                context={context}
                onChange={(nextValue) => {
                  const next = [...entries];
                  next[index] = [key, nextValue];
                  updateEntries(next);
                }}
              />
            </div>

            <ActionIcon
              variant="subtle"
              color="red"
              aria-label="Remove mapping"
              onClick={() =>
                updateEntries(
                  entries.filter(
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
          updateEntries([
            ...entries,
            [
              `key_${entries.length + 1}`,
              getInitialValue(valueSchema),
            ],
          ])
        }
      >
        Add mapping
      </Button>
    </Stack>
  );
}

function ObjectEditor({
  field,
  value,
  context,
  onChange,
}: FieldEditorProps) {
  const objectValue = asRecord(value);

  return (
    <Stack gap="xs">
      {field.properties.map((property) => (
        <FieldEditor
          key={property.key}
          field={property}
          value={objectValue[property.key]}
          context={context}
          onChange={(nextValue) =>
            onChange({
              ...objectValue,
              [property.key]: nextValue,
            })
          }
        />
      ))}
    </Stack>
  );
}

function FieldEditorControl({
  field,
  value,
  context,
  onChange,
}: FieldEditorProps) {
  if (field.constValue !== undefined) {
    return (
      <TextInput
        value={String(field.constValue)}
        disabled
      />
    );
  }

  switch (field.editor) {
    case "checkbox":
      return (
        <Checkbox
          checked={value === true}
          onChange={(event) =>
            onChange(event.currentTarget.checked)
          }
        />
      );

    case "number":
      return (
        <NumberInput
          value={typeof value === "number" ? value : ""}
          allowDecimal={field.type !== "integer"}
          onChange={(nextValue) =>
            onChange(
              typeof nextValue === "number"
                ? nextValue
                : undefined,
            )
          }
        />
      );

    case "select":
      if (field.source === "sheets") {
        return (
          <SheetSelectEditor
            field={field}
            value={value}
            context={context}
            onChange={onChange}
          />
        );
      }

      return (
        <Select
          searchable
          clearable={!field.required}
          value={typeof value === "string" && value ? value : null}
          data={field.enum ?? []}
          onChange={(nextValue) =>
            onChange(nextValue ?? undefined)
          }
        />
      );

    case "column-select":
      return (
        <ColumnSelectEditor
          field={field}
          value={value}
          context={context}
          onChange={onChange}
        />
      );

    case "column-multiselect":
      return (
        <ColumnMultiSelectEditor
          field={field}
          value={value}
          context={context}
          onChange={onChange}
        />
      );

    case "mapping-builder":
      return (
        <MappingEditor
          field={field}
          value={value}
          context={context}
          onChange={onChange}
        />
      );

    case "list-builder":
      if (
        context.stepKey === "reorder_columns" &&
        field.key === "columns"
      ) {
        return (
          <OrderedColumnListEditor
            field={field}
            value={value}
            context={context}
            onChange={onChange}
          />
        );
      }

      if (
        field.items?.type === "object" ||
        (field.items?.properties.length ?? 0) > 0
      ) {
        return (
          <ObjectListEditor
            field={field}
            value={value}
            context={context}
            onChange={onChange}
          />
        );
      }

      return (
        <StringListEditor
          field={field.items ?? field}
          value={value}
          context={context}
          onChange={onChange}
        />
      );

    case "object-editor":
      return (
        <ObjectEditor
          field={field}
          value={value}
          context={context}
          onChange={onChange}
        />
      );

    case "expression-builder":
      return (
        <ExpressionEditor
          value={value}
          columns={context.inputColumns}
          onChange={onChange}
        />
      );

    case "condition-builder":
      return (
        <ConditionEditor
          value={value}
          columns={context.inputColumns}
          onChange={onChange}
        />
      );

    case "value-editor":
      return (
        <LiteralValueEditor
          value={value}
          onChange={onChange}
        />
      );

    case "date-picker":
      return (
        <TextInput
          type="date"
          value={typeof value === "string" ? value : ""}
          onChange={(event) =>
            onChange(event.currentTarget.value || undefined)
          }
        />
      );

    case "datetime-picker":
      return (
        <TextInput
          type="datetime-local"
          value={typeof value === "string" ? value : ""}
          onChange={(event) =>
            onChange(event.currentTarget.value || undefined)
          }
        />
      );

    case "file-picker":
    case "folder-picker":
      return (
        <TextInput
          value={typeof value === "string" ? value : ""}
          placeholder={
            field.editor === "folder-picker"
              ? "Folder path"
              : "File path"
          }
          description="Path on the machine running Crucible."
          onChange={(event) =>
            onChange(event.currentTarget.value || undefined)
          }
        />
      );

    default:
      return (
        <TextInput
          value={
            typeof value === "string" ||
            typeof value === "number"
              ? String(value)
              : ""
          }
          onChange={(event) =>
            onChange(event.currentTarget.value || undefined)
          }
        />
      );
  }
}

export function FieldEditor(props: FieldEditorProps) {
  const { field, value } = props;
  const stableField = useMemo(() => field, [field]);

  return (
    <FieldFrame field={stableField} value={value}>
      <FieldEditorControl {...props} field={stableField} />
    </FieldFrame>
  );
}

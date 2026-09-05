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

import { LiteralValueEditor } from "./literal_value_editor";

export type ExpressionValue =
  | { column: string }
  | { value: unknown }
  | { op: string; args: ExpressionValue[] };

type ExpressionEditorProps = {
  value: unknown;
  columns: string[];
  onChange: (value: ExpressionValue) => void;
  compact?: boolean;
};

const operations = [
  "add",
  "subtract",
  "multiply",
  "divide",
  "safe_divide",
  "round",
  "abs",
  "concat",
  "coalesce",
  "upper",
  "lower",
  "trim",
];

function isExpression(value: unknown): value is ExpressionValue {
  return (
    value !== null &&
    typeof value === "object" &&
    (
      "column" in value ||
      "value" in value ||
      "op" in value
    )
  );
}

function getExpressionKind(
  value: ExpressionValue,
): "column" | "literal" | "operation" {
  if ("column" in value) {
    return "column";
  }

  if ("op" in value) {
    return "operation";
  }

  return "literal";
}

function createExpression(
  kind: "column" | "literal" | "operation",
): ExpressionValue {
  switch (kind) {
    case "column":
      return { column: "" };
    case "operation":
      return {
        op: "add",
        args: [{ column: "" }, { value: 0 }],
      };
    default:
      return { value: "" };
  }
}

export function ExpressionEditor({
  value,
  columns,
  onChange,
  compact = false,
}: ExpressionEditorProps) {
  if (!isExpression(value)) {
    return (
      <Button
        size="xs"
        variant="light"
        onClick={() => onChange({ column: "" })}
      >
        Create expression
      </Button>
    );
  }

  const kind = getExpressionKind(value);

  return (
    <Paper withBorder p={compact ? "xs" : "sm"}>
      <Stack gap="xs">
        <Select
          label={compact ? undefined : "Expression type"}
          value={kind}
          data={[
            { value: "column", label: "Column" },
            { value: "literal", label: "Literal value" },
            { value: "operation", label: "Operation" },
          ]}
          allowDeselect={false}
          onChange={(nextKind) => {
            if (nextKind !== null) {
              onChange(
                createExpression(
                  nextKind as "column" | "literal" | "operation",
                ),
              );
            }
          }}
        />

        {kind === "column" && "column" in value && (
          columns.length > 0 ? (
            <Select
              label="Column"
              searchable
              clearable
              value={value.column || null}
              data={Array.from(
                new Set([
                  ...columns,
                  ...(value.column ? [value.column] : []),
                ]),
              )}
              onChange={(column) =>
                onChange({ column: column ?? "" })
              }
            />
          ) : (
            <TextInput
              label="Column"
              description="Input schema is not available; enter a column name."
              value={value.column}
              onChange={(event) =>
                onChange({ column: event.currentTarget.value })
              }
            />
          )
        )}

        {kind === "literal" && "value" in value && (
          <LiteralValueEditor
            value={value.value}
            onChange={(literal) =>
              onChange({ value: literal })
            }
          />
        )}

        {kind === "operation" && "op" in value && (
          <Stack gap="xs">
            <Select
              label="Operation"
              searchable
              value={value.op}
              data={operations}
              onChange={(operation) =>
                onChange({
                  ...value,
                  op: operation ?? "add",
                })
              }
            />

            <Text size="xs" c="dimmed">
              Arguments
            </Text>

            {value.args.map((argument, index) => (
              <Group
                key={index}
                align="flex-start"
                wrap="nowrap"
              >
                <div className="step-editor-grow">
                  <ExpressionEditor
                    value={argument}
                    columns={columns}
                    compact
                    onChange={(nextArgument) => {
                      const args = [...value.args];
                      args[index] = nextArgument;
                      onChange({ ...value, args });
                    }}
                  />
                </div>

                <ActionIcon
                  variant="subtle"
                  color="red"
                  aria-label="Remove argument"
                  onClick={() =>
                    onChange({
                      ...value,
                      args: value.args.filter(
                        (_, itemIndex) => itemIndex !== index,
                      ),
                    })
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
                onChange({
                  ...value,
                  args: [...value.args, { column: "" }],
                })
              }
            >
              Add argument
            </Button>
          </Stack>
        )}
      </Stack>
    </Paper>
  );
}

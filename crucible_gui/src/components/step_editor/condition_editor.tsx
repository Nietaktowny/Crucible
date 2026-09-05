import {
  ActionIcon,
  Button,
  Group,
  Paper,
  Select,
  Stack,
  Text,
} from "@mantine/core";

import {
  ExpressionEditor,
  type ExpressionValue,
} from "./expression_editor";

type ComparisonCondition = {
  left: ExpressionValue;
  operator: string;
  right?: ExpressionValue | null;
};

type LogicalCondition =
  | {
      logic: "and" | "or";
      conditions: ConditionValue[];
    }
  | {
      logic: "not";
      condition: ConditionValue;
    };

export type ConditionValue =
  | ComparisonCondition
  | LogicalCondition;

type ConditionEditorProps = {
  value: unknown;
  columns: string[];
  onChange: (value: ConditionValue) => void;
  nested?: boolean;
};

const operators = [
  "=",
  "!=",
  ">",
  ">=",
  "<",
  "<=",
  "contains",
  "starts_with",
  "ends_with",
  "is_null",
  "is_not_null",
  "is_in",
];

const unaryOperators = new Set([
  "is_null",
  "is_not_null",
]);

function isCondition(value: unknown): value is ConditionValue {
  return (
    value !== null &&
    typeof value === "object" &&
    ("logic" in value || "operator" in value)
  );
}

function getKind(
  value: ConditionValue,
): "comparison" | "and" | "or" | "not" {
  return "logic" in value ? value.logic : "comparison";
}

function createComparison(): ComparisonCondition {
  return {
    left: { column: "" },
    operator: "=",
    right: { value: "" },
  };
}

function createCondition(
  kind: "comparison" | "and" | "or" | "not",
): ConditionValue {
  if (kind === "and" || kind === "or") {
    return {
      logic: kind,
      conditions: [createComparison()],
    };
  }

  if (kind === "not") {
    return {
      logic: "not",
      condition: createComparison(),
    };
  }

  return createComparison();
}

export function ConditionEditor({
  value,
  columns,
  onChange,
  nested = false,
}: ConditionEditorProps) {
  if (!isCondition(value)) {
    return (
      <Button
        size="xs"
        variant="light"
        onClick={() => onChange(createComparison())}
      >
        Create condition
      </Button>
    );
  }

  const kind = getKind(value);

  return (
    <Paper withBorder p={nested ? "xs" : "sm"}>
      <Stack gap="xs">
        <Select
          label={nested ? undefined : "Condition type"}
          value={kind}
          data={[
            { value: "comparison", label: "Comparison" },
            { value: "and", label: "All conditions (AND)" },
            { value: "or", label: "Any condition (OR)" },
            { value: "not", label: "Negation (NOT)" },
          ]}
          allowDeselect={false}
          onChange={(nextKind) => {
            if (nextKind !== null) {
              onChange(
                createCondition(
                  nextKind as
                    | "comparison"
                    | "and"
                    | "or"
                    | "not",
                ),
              );
            }
          }}
        />

        {kind === "comparison" && !("logic" in value) && (
          <Stack gap="xs">
            <Text size="xs" c="dimmed">
              Left expression
            </Text>
            <ExpressionEditor
              value={value.left}
              columns={columns}
              compact
              onChange={(left) =>
                onChange({ ...value, left })
              }
            />

            <Select
              label="Operator"
              searchable
              value={value.operator}
              data={operators}
              onChange={(operator) => {
                const nextOperator = operator ?? "=";
                onChange({
                  ...value,
                  operator: nextOperator,
                  right: unaryOperators.has(nextOperator)
                    ? null
                    : value.right ?? { value: "" },
                });
              }}
            />

            {!unaryOperators.has(value.operator) && (
              <>
                <Text size="xs" c="dimmed">
                  Right expression
                </Text>
                <ExpressionEditor
                  value={value.right}
                  columns={columns}
                  compact
                  onChange={(right) =>
                    onChange({ ...value, right })
                  }
                />
              </>
            )}
          </Stack>
        )}

        {(kind === "and" || kind === "or") &&
          "logic" in value &&
          value.logic !== "not" && (
            <Stack gap="xs">
              {value.conditions.map((condition, index) => (
                <Group
                  key={index}
                  align="flex-start"
                  wrap="nowrap"
                >
                  <div className="step-editor-grow">
                    <ConditionEditor
                      value={condition}
                      columns={columns}
                      nested
                      onChange={(nextCondition) => {
                        const conditions = [...value.conditions];
                        conditions[index] = nextCondition;
                        onChange({ ...value, conditions });
                      }}
                    />
                  </div>

                  <ActionIcon
                    variant="subtle"
                    color="red"
                    aria-label="Remove condition"
                    onClick={() =>
                      onChange({
                        ...value,
                        conditions: value.conditions.filter(
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
                    conditions: [
                      ...value.conditions,
                      createComparison(),
                    ],
                  })
                }
              >
                Add condition
              </Button>
            </Stack>
          )}

        {kind === "not" &&
          "logic" in value &&
          value.logic === "not" && (
            <ConditionEditor
              value={value.condition}
              columns={columns}
              nested
              onChange={(condition) =>
                onChange({ ...value, condition })
              }
            />
          )}
      </Stack>
    </Paper>
  );
}

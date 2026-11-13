import { useContext, useEffect, useRef, useState } from "react";
import {
  Button,
  Group,
  NumberInput,
  SegmentedControl,
  Select,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";

import { ClientContext } from "@/context/api_context";
import { ConditionEditor } from "@/components/step_editor/condition_editor";
import { LiteralValueEditor } from "@/components/step_editor/literal_value_editor";
import type { WorkflowConfig } from "@/types/workflows";
import { getErrorMessage } from "@/lib/format";
import { valueCondition, valueExpression } from "./model";

import { FilterValueSelect } from "./filter_value_select";

type Rule = { column: string; operator: string; value: unknown };
type Props = {
  workflowName: string;
  workflow: WorkflowConfig;
  targetId: string | null;
  before: boolean;
  schema: Record<string, string>;
  initialColumn?: string;
  value: unknown;
  onChange: (value: unknown) => void;
};

const unary = ["is_null", "is_not_null"];
const basicOperators = [
  "=",
  "!=",
  ">",
  ">=",
  "<",
  "<=",
  "contains",
  "starts_with",
  "ends_with",
  ...unary,
];

function simpleRules(value: unknown): Rule[] | null {
  if (!value || typeof value !== "object") return null;
  const condition = value as Record<string, unknown>;
  if (condition.logic === "and" || condition.logic === "or") {
    if (!Array.isArray(condition.conditions)) return null;
    const children = condition.conditions.map(simpleRules);
    return children.every((child) => child?.length === 1)
      ? children.flatMap((child) => child ?? [])
      : null;
  }
  const left = condition.left as { column?: string } | undefined;
  const right = condition.right as { value?: unknown } | undefined;
  return left?.column &&
    typeof condition.operator === "string" &&
    basicOperators.includes(condition.operator) &&
    condition.operator !== "contains" &&
    (unary.includes(condition.operator) || (right && "value" in right))
    ? [
        {
          column: left.column,
          operator: condition.operator,
          value: right?.value ?? null,
        },
      ]
    : null;
}

function defaultValue(dtype = ""): unknown {
  return /^(Int|UInt|Float|Decimal)/.test(dtype)
    ? 0
    : dtype === "Boolean"
      ? false
      : "";
}

export function FilterEditor({
  workflowName,
  workflow,
  targetId,
  before,
  schema,
  initialColumn,
  value,
  onChange,
}: Props) {
  const client = useContext(ClientContext);
  const initialRules = simpleRules(value);
  const initialLogic =
    value && typeof value === "object" && "logic" in value ? value.logic : null;
  const initialValues =
    initialRules &&
    initialLogic !== "and" &&
    initialRules.every(
      (rule) =>
        rule.column === initialRules[0].column &&
        ["=", "is_null"].includes(rule.operator),
    )
      ? initialRules.map((rule) => rule.value)
      : null;
  const [mode, setMode] = useState(
    value
      ? initialValues
        ? "values"
        : initialRules
          ? "conditions"
          : "advanced"
      : "values",
  );
  const [column, setColumn] = useState(
    initialColumn ?? initialRules?.[0]?.column ?? Object.keys(schema)[0] ?? "",
  );
  const [search, setSearch] = useState("");
  const [values, setValues] = useState<unknown[]>([]);
  const [chosen, setChosen] = useState<unknown[]>(initialValues ?? []);
  const [truncated, setTruncated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logic, setLogic] = useState(initialLogic === "or" ? "or" : "and");
  const [rules, setRules] = useState<Rule[]>(
    initialRules ?? [
      { column, operator: "=", value: defaultValue(schema[column]) },
    ],
  );
  const generation = useRef(0);

  useEffect(() => {
    const id = ++generation.current;
    if (!targetId || !column || mode !== "values") return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      setError(null);
      void client
        .filterValues(
          workflowName,
          workflow,
          targetId,
          column,
          search,
          before,
          controller.signal,
        )
        .then((result) => {
          if (id !== generation.current) return;
          setValues(result.values);
          setTruncated(result.truncated);
        })
        .catch((reason: unknown) => {
          if (!controller.signal.aborted && id === generation.current)
            setError(getErrorMessage(reason));
        })
        .finally(() => {
          if (id === generation.current) setLoading(false);
        });
    }, 250);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
      generation.current = id + 1;
    };
  }, [client, workflowName, workflow, targetId, column, search, before, mode]);

  function emitRules(next: Rule[], nextLogic = logic) {
    setRules(next);
    const conditions = next.map((rule) => ({
      left: { column: rule.column },
      operator: rule.operator,
      ...(unary.includes(rule.operator)
        ? {}
        : {
            right: valueExpression(
              rule.operator === "contains" && typeof rule.value === "string"
                ? rule.value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
                : rule.value,
              schema[rule.column],
            ),
          }),
    }));
    onChange(
      conditions.length === 1
        ? conditions[0]
        : { logic: nextLogic, conditions },
    );
  }

  function choose(next: unknown[]) {
    setChosen(next);
    const conditions = next.map((item) =>
      valueCondition(column, item, schema[column]),
    );
    onChange(
      conditions.length === 0
        ? { left: { column }, operator: "is_in", right: { value: [] } }
        : conditions.length === 1
          ? conditions[0]
          : { logic: "or", conditions },
    );
  }

  return (
    <Stack gap="sm">
      <SegmentedControl
        value={mode}
        onChange={setMode}
        data={[
          { value: "values", label: "Values" },
          { value: "conditions", label: "Conditions" },
          { value: "advanced", label: "Advanced" },
        ]}
      />
      {value !== undefined && mode !== "advanced" && (
        <Text size="xs" c="dimmed">
          Changes here replace this step’s condition. Cancel keeps its original
          settings.
        </Text>
      )}
      {mode === "values" && (
        <>
          <Select
            label="Column"
            data={Object.keys(schema)}
            value={column}
            allowDeselect={false}
            onChange={(next) => {
              setColumn(next ?? "");
              setChosen([]);
              setValues([]);
              setSearch("");
            }}
          />
          <FilterValueSelect
            values={values}
            chosen={chosen}
            search={search}
            loading={loading}
            error={error}
            truncated={truncated}
            onSearch={setSearch}
            onChange={choose}
          />
        </>
      )}
      {mode === "conditions" && (
        <>
          <Select
            label="Match"
            value={logic}
            data={[
              { value: "and", label: "All conditions (AND)" },
              { value: "or", label: "Any condition (OR)" },
            ]}
            onChange={(next) => {
              setLogic(next ?? "and");
              emitRules(rules, next ?? "and");
            }}
          />
          {rules.map((rule, index) => {
            const update = (change: Partial<Rule>) =>
              emitRules(
                rules.map((item, i) =>
                  i === index ? { ...item, ...change } : item,
                ),
              );
            const dtype = schema[rule.column] ?? "";
            const operators = /^(String|Categorical|Enum)/.test(dtype)
              ? basicOperators
              : basicOperators.filter(
                  (operator) =>
                    !["contains", "starts_with", "ends_with"].includes(
                      operator,
                    ),
                );
            return (
              <Stack key={index} gap="xs" p="sm" className="fire-panel">
                <Select
                  label="Column"
                  data={Object.keys(schema)}
                  value={rule.column}
                  onChange={(next) =>
                    update({
                      column: next ?? "",
                      value: defaultValue(schema[next ?? ""]),
                    })
                  }
                />
                <Select
                  label="Operator"
                  data={operators}
                  value={rule.operator}
                  onChange={(next) => update({ operator: next ?? "=" })}
                />
                {!unary.includes(rule.operator) &&
                  (/^(Date|Time)/.test(dtype) ? (
                    <TextInput
                      label="ISO date/time value"
                      value={String(rule.value ?? "")}
                      onChange={(event) =>
                        update({ value: event.currentTarget.value })
                      }
                    />
                  ) : /^(Int|UInt|Float|Decimal)/.test(dtype) ? (
                    <NumberInput
                      label="Value"
                      value={
                        typeof rule.value === "number"
                          ? rule.value
                          : String(rule.value ?? "")
                      }
                      onChange={(next) => update({ value: next })}
                    />
                  ) : dtype === "Boolean" ? (
                    <Select
                      label="Value"
                      data={[
                        { value: "true", label: "True" },
                        { value: "false", label: "False" },
                      ]}
                      value={String(rule.value)}
                      onChange={(next) => update({ value: next === "true" })}
                    />
                  ) : (
                    <LiteralValueEditor
                      value={rule.value}
                      onChange={(next) => update({ value: next })}
                    />
                  ))}
                {rules.length > 1 && (
                  <Button
                    variant="subtle"
                    color="red"
                    size="xs"
                    onClick={() =>
                      emitRules(rules.filter((_, i) => i !== index))
                    }
                  >
                    Remove condition
                  </Button>
                )}
              </Stack>
            );
          })}
          <Button
            size="xs"
            variant="default"
            onClick={() =>
              emitRules([
                ...rules,
                { column, operator: "=", value: defaultValue(schema[column]) },
              ])
            }
          >
            Add condition
          </Button>
          <Group>
            <Button
              size="xs"
              variant="light"
              onClick={() =>
                onChange(valueCondition(rules[0]?.column ?? column, null))
              }
            >
              Keep nulls
            </Button>
            <Button
              size="xs"
              variant="light"
              onClick={() =>
                onChange(
                  valueCondition(
                    rules[0]?.column ?? column,
                    null,
                    undefined,
                    true,
                  ),
                )
              }
            >
              Exclude nulls
            </Button>
          </Group>
        </>
      )}
      {mode === "advanced" && (
        <ConditionEditor
          value={value}
          columns={Object.keys(schema)}
          onChange={onChange}
        />
      )}
    </Stack>
  );
}

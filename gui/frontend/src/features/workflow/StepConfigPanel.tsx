import { useState } from "react";
import { stringify } from "yaml";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { stepRegistry, type StepKey } from "@/features/workflow/stepRegistry";
import {
  isMultiSourceStep,
  type WorkflowEditorStep,
  type WorkflowSourceStep,
} from "@/features/workflow/types";

type SourceStep = WorkflowSourceStep;

type StepConfigPanelProps = {
  step: WorkflowEditorStep | null;
  onUpdateParameters: (field: string, value: unknown) => void;
  onUpdateMetadata: (field: "name" | "description", value: string) => void;
  onUpdateSources?: (sources: SourceStep[]) => void;
  onRemoveStep: () => void;
};

declare global {
  interface Window {
    crucible?: {
      version?: string;
      selectFilePath?: () => Promise<string | null>;
      selectDirectoryPath?: () => Promise<string | null>;
    };
  }
}

const LITERAL_OPTIONS: Record<string, string[]> = {
  "remove_duplicates.keep": ["first", "last"],
  "join.how": ["left", "inner", "right", "full", "anti", "cross"],
  "concat.how": ["vertical", "diagonal", "horizontal"],
  "sort_rows.columns.direction": ["asc", "desc"],
  "group_by.aggregations.function": [
    "sum",
    "min",
    "max",
    "mean",
    "median",
    "count",
    "len",
    "first",
    "last",
    "n_unique",
  ],
  "date_add.unit": ["days", "hours", "minutes", "seconds", "milliseconds"],
  "date_diff.unit": ["days", "hours", "minutes", "seconds", "milliseconds"],
  "date_period_filter.period": [
    "current_year",
    "current_month",
    "current_day",
  ],
  "date_range_filter.value_type": ["date", "datetime"],
  "date_range_filter.closed": ["both", "left", "right", "none"],
  "extract_datetime_part.part": [
    "year",
    "month",
    "day",
    "week",
    "weekday",
    "hour",
    "minute",
    "second",
  ],
  "extract_date_time.extract": ["date", "time"],
};

const FILTER_OPERATORS = [
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
];

type FilterSideKind = "column" | "value";

const POLARS_TYPE_OPTIONS = [
  "string",
  "text",
  "int8",
  "int16",
  "int32",
  "int64",
  "uint8",
  "uint16",
  "uint32",
  "uint64",
  "float32",
  "float64",
  "boolean",
  "date",
  "datetime",
  "time",
];

const MULTI_SOURCE_DEFAULT_ALIAS: Record<string, string> = {
  join: "right",
  concat: "source",
};

function getLiteralOptions(stepKey: string, path: string[]): string[] | null {
  const fieldPath = path.join(".");

  if (stepKey === "change_column_type" && fieldPath === "column_types") {
    return POLARS_TYPE_OPTIONS;
  }

  return LITERAL_OPTIONS[`${stepKey}.${fieldPath}`] ?? null;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringList(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isPrimitive(value: unknown) {
  return (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean" ||
    value === null ||
    value === undefined
  );
}

function isPrimitiveRecord(value: unknown): value is Record<string, unknown> {
  return (
    isPlainObject(value) &&
    Object.values(value).every((item) => isPrimitive(item))
  );
}

function isPathField(field: string) {
  return (
    field === "path" ||
    field.endsWith("_path") ||
    field.includes("file") ||
    field.includes("folder") ||
    field.includes("directory")
  );
}

function isFolderPathField(stepKey: string, field: string) {
  return (
    stepKey.includes("folder") ||
    field.includes("folder") ||
    field.includes("directory")
  );
}

function parsePrimitiveValue(value: string, previousValue: unknown): unknown {
  if (typeof previousValue === "number") {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? value : parsed;
  }

  if (typeof previousValue === "boolean") {
    return value === "true";
  }

  if (previousValue === null || previousValue === undefined) {
    if (value === "" || value === "null") return null;
    if (value === "true") return true;
    if (value === "false") return false;

    const parsed = Number(value);
    return !Number.isNaN(parsed) && value.trim() !== "" ? parsed : value;
  }

  return value;
}

function makeId() {
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;
}

async function selectPath(kind: "file" | "directory") {
  if (kind === "directory" && window.crucible?.selectDirectoryPath) {
    return window.crucible.selectDirectoryPath();
  }

  if (kind === "file" && window.crucible?.selectFilePath) {
    return window.crucible.selectFilePath();
  }

  return window.prompt(
    kind === "directory" ? "Paste folder path:" : "Paste file path:",
  );
}

function FieldLabel({ children }: { children: string }) {
  return (
    <div className="text-xs font-medium text-muted-foreground">{children}</div>
  );
}

function EmptyHint({ children }: { children: string }) {
  return (
    <div className="rounded-md border border-dashed p-3 text-xs text-muted-foreground">
      {children}
    </div>
  );
}

function SelectInput({
  value,
  options,
  onChange,
}: {
  value: unknown;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <select
      className="h-10 w-full rounded-md border bg-background px-3 text-sm text-foreground"
      value={String(value ?? options[0] ?? "")}
      onChange={(event) => onChange(event.target.value)}
    >
      {options.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </select>
  );
}

function PrimitiveValueInput({
  value,
  options,
  onChange,
}: {
  value: unknown;
  options?: string[] | null;
  onChange: (value: unknown) => void;
}) {
  if (options) {
    return <SelectInput value={value} options={options} onChange={onChange} />;
  }

  if (typeof value === "boolean") {
    return (
      <SelectInput
        value={String(value)}
        options={["true", "false"]}
        onChange={(next) => onChange(next === "true")}
      />
    );
  }

  return (
    <Input
      value={String(value ?? "")}
      placeholder="Value"
      onChange={(event) =>
        onChange(parsePrimitiveValue(event.target.value, value))
      }
    />
  );
}

function readFilterCondition(value: unknown) {
  const condition = isPlainObject(value) ? value : {};

  const left = isPlainObject(condition.left) ? condition.left : {};
  const right = isPlainObject(condition.right) ? condition.right : {};

  return {
    leftKind: (left.column !== undefined ? "column" : "value") as FilterSideKind,
    leftValue: String(left.column ?? left.value ?? ""),
    operator: String(condition.operator ?? "="),
    rightKind: (right.column !== undefined ? "column" : "value") as FilterSideKind,
    rightValue: String(right.column ?? right.value ?? ""),
  };
}

function buildFilterSide(kind: FilterSideKind, value: string) {
  return kind === "column" ? { column: value } : { value };
}

function FilterConditionEditor({
  value,
  onChange,
}: {
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  const condition = readFilterCondition(value);

  function update(next: Partial<typeof condition>) {
    const merged = { ...condition, ...next };

    onChange({
      left: buildFilterSide(merged.leftKind, merged.leftValue),
      operator: merged.operator,
      right: buildFilterSide(merged.rightKind, merged.rightValue),
    });
  }

  return (
    <div className="space-y-3 rounded-md border bg-background p-3">
      <div className="space-y-2">
        <FieldLabel>Left side</FieldLabel>

        <div className="grid grid-cols-[130px_1fr] gap-2">
          <SelectInput
            value={condition.leftKind}
            options={["column", "value"]}
            onChange={(next) => update({ leftKind: next as FilterSideKind })}
          />

          <Input
            value={condition.leftValue}
            placeholder={condition.leftKind === "column" ? "Column name" : "Value"}
            onChange={(event) => update({ leftValue: event.target.value })}
          />
        </div>
      </div>

      <div className="space-y-2">
        <FieldLabel>Operator</FieldLabel>

        <SelectInput
          value={condition.operator}
          options={FILTER_OPERATORS}
          onChange={(next) => update({ operator: next })}
        />
      </div>

      <div className="space-y-2">
        <FieldLabel>Right side</FieldLabel>

        <div className="grid grid-cols-[130px_1fr] gap-2">
          <SelectInput
            value={condition.rightKind}
            options={["value", "column"]}
            onChange={(next) => update({ rightKind: next as FilterSideKind })}
          />

          <Input
            value={condition.rightValue}
            placeholder={condition.rightKind === "column" ? "Column name" : "Value"}
            onChange={(event) => update({ rightValue: event.target.value })}
          />
        </div>
      </div>
    </div>
  );
}

function PathEditor({
  stepKey,
  path,
  value,
  onChange,
}: {
  stepKey: string;
  path: string[];
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  const field = path.at(-1) ?? "";
  const kind = isFolderPathField(stepKey, field) ? "directory" : "file";

  return (
    <div className="flex gap-2">
      <Input
        value={String(value ?? "")}
        onChange={(event) => onChange(event.target.value)}
      />

      <Button
        type="button"
        variant="outline"
        onClick={async () => {
          const selected = await selectPath(kind);
          if (selected) onChange(selected);
        }}
      >
        Browse
      </Button>
    </div>
  );
}

function StringOrStringListEditor({
  value,
  onChange,
}: {
  value: string | string[];
  onChange: (value: string | string[]) => void;
}) {
  const mode = Array.isArray(value) ? "list" : "single";
  const values = Array.isArray(value) ? value : [value];

  return (
    <div className="space-y-2">
      <SelectInput
        value={mode}
        options={["single", "list"]}
        onChange={(nextMode) => {
          if (nextMode === "single") onChange(values[0] ?? "");
          else onChange(values);
        }}
      />

      {mode === "single" ? (
        <Input
          value={String(value ?? "")}
          onChange={(event) => onChange(event.target.value)}
        />
      ) : (
        <StringListEditor value={values} onChange={onChange} />
      )}
    </div>
  );
}

function StringListEditor({
  value,
  onChange,
}: {
  value: string[];
  onChange: (value: string[]) => void;
}) {
  function updateItem(index: number, nextValue: string) {
    onChange(
      value.map((item, currentIndex) =>
        currentIndex === index ? nextValue : item,
      ),
    );
  }

  function removeItem(index: number) {
    onChange(value.filter((_, currentIndex) => currentIndex !== index));
  }

  function moveItem(index: number, direction: -1 | 1) {
    const targetIndex = index + direction;

    if (targetIndex < 0 || targetIndex >= value.length) {
      return;
    }

    const next = [...value];
    const [removed] = next.splice(index, 1);
    next.splice(targetIndex, 0, removed);
    onChange(next);
  }

  return (
    <div className="space-y-2">
      {value.length === 0 && <EmptyHint>Empty list.</EmptyHint>}

      {value.map((item, index) => (
        <div key={index} className="grid grid-cols-[auto_1fr_auto] gap-2">
          <div className="flex gap-1">
            <Button
              type="button"
              variant="outline"
              disabled={index === 0}
              onClick={() => moveItem(index, -1)}
            >
              ↑
            </Button>

            <Button
              type="button"
              variant="outline"
              disabled={index === value.length - 1}
              onClick={() => moveItem(index, 1)}
            >
              ↓
            </Button>
          </div>

          <Input
            value={item}
            placeholder="Column"
            onChange={(event) => updateItem(index, event.target.value)}
          />

          <Button
            type="button"
            variant="outline"
            onClick={() => removeItem(index)}
          >
            Remove
          </Button>
        </div>
      ))}

      <Button
        type="button"
        variant="outline"
        className="w-full"
        onClick={() => onChange([...value, ""])}
      >
        Add value
      </Button>
    </div>
  );
}

function PrimitiveRecordEditor({
  stepKey,
  path,
  value,
  onChange,
}: {
  stepKey: string;
  path: string[];
  value: Record<string, unknown>;
  onChange: (value: Record<string, unknown>) => void;
}) {
  const entries = Object.entries(value);

  function updateEntry(index: number, key: string, entryValue: unknown) {
    const nextEntries = entries.map(([currentKey, currentValue], currentIndex) =>
      currentIndex === index ? [key, entryValue] : [currentKey, currentValue],
    );

    onChange(Object.fromEntries(nextEntries.filter(([nextKey]) => nextKey)));
  }

  function addEntry() {
    let key = "new_key";
    let counter = 1;

    while (Object.prototype.hasOwnProperty.call(value, key)) {
      key = `new_key_${counter}`;
      counter += 1;
    }

    onChange({ ...value, [key]: "" });
  }

  return (
    <div className="space-y-2">
      {entries.length === 0 && <EmptyHint>Empty dictionary.</EmptyHint>}

      {entries.map(([key, entryValue], index) => (
        <div
          key={`${key}-${index}`}
          className="grid grid-cols-[1fr_1fr_auto] gap-2"
        >
          <Input
            value={key}
            placeholder="Key"
            onChange={(event) =>
              updateEntry(index, event.target.value, entryValue)
            }
          />

          <ConfigValueEditor
            stepKey={stepKey}
            path={[...path, key]}
            value={entryValue}
            onChange={(nextValue) => updateEntry(index, key, nextValue)}
          />

          <Button
            type="button"
            variant="outline"
            onClick={() => {
              onChange(
                Object.fromEntries(
                  entries.filter((_, currentIndex) => currentIndex !== index),
                ),
              );
            }}
          >
            Remove
          </Button>
        </div>
      ))}

      <Button
        type="button"
        variant="outline"
        className="w-full"
        onClick={addEntry}
      >
        Add item
      </Button>
    </div>
  );
}

function ObjectListEditor({
  stepKey,
  path,
  value,
  onChange,
}: {
  stepKey: string;
  path: string[];
  value: Record<string, unknown>[];
  onChange: (value: Record<string, unknown>[]) => void;
}) {
  function makeDefaultItem(): Record<string, unknown> {
    const field = path.at(-1);

    if (stepKey === "sort_rows" && field === "columns") {
      return { name: "", direction: "asc" };
    }

    if (stepKey === "group_by" && field === "aggregations") {
      return { column: "", function: "sum", alias: null };
    }

    return {};
  }

  function updateItem(index: number, nextItem: Record<string, unknown>) {
    onChange(
      value.map((item, currentIndex) =>
        currentIndex === index ? nextItem : item,
      ),
    );
  }

  function removeItem(index: number) {
    onChange(value.filter((_, currentIndex) => currentIndex !== index));
  }

  function moveItem(index: number, direction: -1 | 1) {
    const targetIndex = index + direction;

    if (targetIndex < 0 || targetIndex >= value.length) {
      return;
    }

    const next = [...value];
    const [removed] = next.splice(index, 1);
    next.splice(targetIndex, 0, removed);
    onChange(next);
  }

  return (
    <div className="space-y-3">
      {value.length === 0 && <EmptyHint>Empty list.</EmptyHint>}

      {value.map((item, index) => (
        <div key={index} className="rounded-md border bg-background p-3">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div className="text-xs font-medium text-muted-foreground">
              Item {index + 1}
            </div>

            <div className="flex gap-1">
              <Button
                type="button"
                variant="outline"
                disabled={index === 0}
                onClick={() => moveItem(index, -1)}
              >
                ↑
              </Button>

              <Button
                type="button"
                variant="outline"
                disabled={index === value.length - 1}
                onClick={() => moveItem(index, 1)}
              >
                ↓
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={() => removeItem(index)}
              >
                Remove
              </Button>
            </div>
          </div>

          <ObjectEditor
            stepKey={stepKey}
            path={path}
            value={item}
            onChange={(nextItem) => updateItem(index, nextItem)}
          />
        </div>
      ))}

      <Button
        type="button"
        variant="outline"
        className="w-full"
        onClick={() => onChange([...value, makeDefaultItem()])}
      >
        Add item
      </Button>
    </div>
  );
}

function ObjectEditor({
  stepKey,
  path,
  value,
  onChange,
}: {
  stepKey: string;
  path: string[];
  value: Record<string, unknown>;
  onChange: (value: Record<string, unknown>) => void;
}) {
  return (
    <div className="space-y-3">
      {Object.entries(value).map(([field, fieldValue]) => (
        <div key={field} className="space-y-2">
          <FieldLabel>{field}</FieldLabel>

          <ConfigValueEditor
            stepKey={stepKey}
            path={[...path, field]}
            value={fieldValue}
            onChange={(nextValue) => onChange({ ...value, [field]: nextValue })}
          />
        </div>
      ))}
    </div>
  );
}

function ComplexYamlEditor({
  value,
  onChange,
}: {
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  return (
    <textarea
      className="min-h-40 w-full rounded-md border bg-background px-3 py-2 font-mono text-xs text-foreground"
      value={stringify(value, {
        indent: 2,
        lineWidth: 0,
        nullStr: "null",
      })}
      onChange={(event) => {
        try {
          onChange(JSON.parse(event.target.value));
        } catch {
          // Invalid JSON while typing.
        }
      }}
    />
  );
}

function ConfigValueEditor({
  stepKey,
  path,
  value,
  onChange,
}: {
  stepKey: string;
  path: string[];
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  const field = path.at(-1) ?? "";
  const literalOptions = getLiteralOptions(stepKey, path);

  if (stepKey === "filter_rows" && path.join(".") === "condition") {
    return <FilterConditionEditor value={value} onChange={onChange} />;
  }

  if (
    stepKey === "join" &&
    (field === "left_on" || field === "right_on") &&
    (typeof value === "string" || isStringList(value))
  ) {
    return (
      <StringOrStringListEditor
        value={value}
        onChange={(nextValue) => onChange(nextValue)}
      />
    );
  }

  if (literalOptions && typeof value === "string") {
    return (
      <PrimitiveValueInput
        value={value}
        options={literalOptions}
        onChange={onChange}
      />
    );
  }

  if (isPathField(field) && typeof value === "string") {
    return (
      <PathEditor
        stepKey={stepKey}
        path={path}
        value={value}
        onChange={onChange}
      />
    );
  }

  if (isStringList(value)) {
    return <StringListEditor value={value} onChange={onChange} />;
  }

  if (Array.isArray(value) && value.every((item) => isPlainObject(item))) {
    return (
      <ObjectListEditor
        stepKey={stepKey}
        path={path}
        value={value as Record<string, unknown>[]}
        onChange={onChange}
      />
    );
  }

  if (isPrimitiveRecord(value)) {
    return (
      <PrimitiveRecordEditor
        stepKey={stepKey}
        path={path}
        value={value}
        onChange={onChange}
      />
    );
  }

  if (isPlainObject(value)) {
    return (
      <ObjectEditor
        stepKey={stepKey}
        path={path}
        value={value}
        onChange={onChange}
      />
    );
  }

  if (Array.isArray(value)) {
    return <ComplexYamlEditor value={value} onChange={onChange} />;
  }

  return (
    <PrimitiveValueInput
      value={value}
      options={literalOptions}
      onChange={onChange}
    />
  );
}

function makeSourceStep(stepKey: StepKey, ownerStepKey: string): SourceStep {
  const registryItem = stepRegistry[stepKey];
  const aliasBase = MULTI_SOURCE_DEFAULT_ALIAS[ownerStepKey] ?? "source";
  const alias = ownerStepKey === "join" ? "right" : `${aliasBase}_${Date.now()}`;

  return {
    id: makeId(),
    key: stepKey,
    name: registryItem.label,
    description: registryItem.description,
    parameters: {
      ...structuredClone(registryItem.defaultConfig),
      context_store: true,
      context_key: alias,
    },
    alias,
  };
}

function SourcesEditor({
  ownerStepKey,
  sources,
  onChange,
}: {
  ownerStepKey: string;
  sources: SourceStep[];
  onChange?: (sources: SourceStep[]) => void;
}) {
  const availableStepKeys = Object.keys(stepRegistry) as StepKey[];
  const canEdit = Boolean(onChange);

  function updateSource(index: number, nextSource: SourceStep) {
    if (!onChange) return;

    onChange(
      sources.map((source, currentIndex) =>
        currentIndex === index ? nextSource : source,
      ),
    );
  }

  function updateSourceParameter(index: number, field: string, value: unknown) {
    const source = sources[index];

    updateSource(index, {
      ...source,
      parameters: {
        ...source.parameters,
        [field]: value,
      },
    });
  }

  function updateAlias(index: number, alias: string) {
    const source = sources[index];

    updateSource(index, {
      ...source,
      alias,
      parameters: {
        ...source.parameters,
        context_store: true,
        context_key: alias,
      },
    });
  }

  function removeSource(index: number) {
    if (!onChange) return;
    onChange(sources.filter((_, currentIndex) => currentIndex !== index));
  }

  function addSource(stepKey: StepKey) {
    if (!onChange) return;
    onChange([...sources, makeSourceStep(stepKey, ownerStepKey)]);
  }

  return (
    <div className="space-y-3">
      {!canEdit && (
        <EmptyHint>
          Source editing requires onUpdateSources in WorkflowEditorPage.
        </EmptyHint>
      )}

      {sources.length === 0 && (
        <EmptyHint>No extra sources configured.</EmptyHint>
      )}

      {sources.map((source, index) => (
        <div
          key={source.id ?? `${source.key}-${index}`}
          className="rounded-md border bg-background p-3"
        >
          <div className="mb-3 flex items-center justify-between gap-2">
            <div>
              <div className="text-sm font-medium">
                {String(index + 1).padStart(2, "0")} · {source.name}
              </div>

              <div className="text-xs text-muted-foreground">{source.key}</div>
            </div>

            <Button
              type="button"
              variant="outline"
              disabled={!canEdit}
              onClick={() => removeSource(index)}
            >
              Remove
            </Button>
          </div>

          <div className="space-y-3">
            <div className="space-y-2">
              <FieldLabel>Source step</FieldLabel>

              <SelectInput
                value={source.key}
                options={availableStepKeys}
                onChange={(nextKey) => {
                  const nextStepKey = nextKey as StepKey;
                  const nextSource = makeSourceStep(nextStepKey, ownerStepKey);

                  updateSource(index, {
                    ...nextSource,
                    id: source.id,
                    alias: source.alias ?? nextSource.alias,
                  });
                }}
              />
            </div>

            <div className="space-y-2">
              <FieldLabel>Alias / context key</FieldLabel>

              <Input
                disabled={!canEdit}
                value={source.alias ?? String(source.parameters?.context_key ?? "")}
                onChange={(event) => updateAlias(index, event.target.value)}
              />
            </div>

            <div className="rounded-md border p-3">
              <div className="mb-3 text-xs font-medium text-muted-foreground">
                Source parameters
              </div>

              <div className="space-y-3">
                {Object.entries(source.parameters ?? {}).map(([field, value]) => (
                  <div key={field} className="space-y-2">
                    <FieldLabel>{field}</FieldLabel>

                    <ConfigValueEditor
                      stepKey={source.key}
                      path={[field]}
                      value={value}
                      onChange={(nextValue) =>
                        updateSourceParameter(index, field, nextValue)
                      }
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ))}

      <AddSourceControl
        disabled={!canEdit || availableStepKeys.length === 0}
        availableStepKeys={availableStepKeys}
        onAdd={addSource}
      />
    </div>
  );
}

function AddSourceControl({
  disabled,
  availableStepKeys,
  onAdd,
}: {
  disabled: boolean;
  availableStepKeys: StepKey[];
  onAdd: (stepKey: StepKey) => void;
}) {
  const [selectedStepKey, setSelectedStepKey] = useState<StepKey>(
    availableStepKeys[0],
  );

  return (
    <div className="flex gap-2">
      <select
        className="h-10 min-w-0 flex-1 rounded-md border bg-background px-3 text-sm text-foreground"
        disabled={disabled}
        value={selectedStepKey}
        onChange={(event) => setSelectedStepKey(event.target.value as StepKey)}
      >
        {availableStepKeys.map((stepKey) => (
          <option key={stepKey} value={stepKey}>
            {stepKey}
          </option>
        ))}
      </select>

      <Button
        type="button"
        variant="outline"
        disabled={disabled}
        onClick={() => onAdd(selectedStepKey)}
      >
        Add source
      </Button>
    </div>
  );
}

export default function StepConfigPanel({
  step,
  onUpdateParameters,
  onUpdateMetadata,
  onUpdateSources,
  onRemoveStep,
}: StepConfigPanelProps) {
  if (!step) {
    return (
      <section className="flex min-h-0 flex-col rounded-lg border bg-card">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">Step Config</h2>
        </div>

        <div className="p-4 text-sm text-muted-foreground">
          Select a step in the graph to edit it.
        </div>
      </section>
    );
  }

  return (
    <section className="flex min-h-0 flex-col rounded-lg border bg-card">
      <div className="border-b px-4 py-3">
        <h2 className="text-sm font-semibold">Step Config</h2>
      </div>

      <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
        <div className="space-y-2">
          <FieldLabel>Step key</FieldLabel>
          <Input value={step.key} disabled />
        </div>

        <div className="space-y-2">
          <FieldLabel>Custom name</FieldLabel>

          <Input
            value={step.name}
            onChange={(event) => onUpdateMetadata("name", event.target.value)}
          />
        </div>

        <div className="space-y-2">
          <FieldLabel>Custom description</FieldLabel>

          <textarea
            className="min-h-24 w-full rounded-md border bg-background px-3 py-2 text-sm text-foreground"
            value={step.description}
            onChange={(event) =>
              onUpdateMetadata("description", event.target.value)
            }
          />
        </div>

        <div className="border-t pt-4">
          <div className="mb-3 text-xs font-medium text-muted-foreground">
            Parameters
          </div>

          <div className="space-y-4">
            {Object.entries(step.parameters).length === 0 && (
              <EmptyHint>This step has no parameters.</EmptyHint>
            )}

            {Object.entries(step.parameters).map(([field, value]) => (
              <div key={field} className="space-y-2">
                <FieldLabel>{field}</FieldLabel>

                <ConfigValueEditor
                  stepKey={step.key}
                  path={[field]}
                  value={value}
                  onChange={(nextValue) => onUpdateParameters(field, nextValue)}
                />
              </div>
            ))}
          </div>
        </div>

        {isMultiSourceStep(step) && (
          <div className="border-t pt-4">
            <div className="mb-3 text-xs font-medium text-muted-foreground">
              Sources
            </div>

            <SourcesEditor
              ownerStepKey={step.key}
              sources={step.sources}
              onChange={onUpdateSources}
            />
          </div>
        )}
      </div>

      <div className="border-t p-4">
        <Button variant="destructive" className="w-full" onClick={onRemoveStep}>
          Remove step
        </Button>
      </div>
    </section>
  );
}
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { JsonSchemaProperty } from "@/lib/crucibleApi";

type SchemaStepConfigEditorProps = {
  schema: JsonSchemaProperty;
  value: Record<string, unknown>;
  onChange: (value: Record<string, unknown>) => void;
  availableColumns?: string[];
};

function getInitialValue(schema: JsonSchemaProperty): unknown {
  if (schema.default !== undefined) return schema.default;

  if (schema.type === "array") return [];
  if (schema.type === "boolean") return false;
  if (schema.type === "integer" || schema.type === "number") return 0;
  if (schema.type === "object") return {};

  return "";
}

export default function SchemaStepConfigEditor({
  schema,
  value,
  onChange,
  availableColumns = [],
}: SchemaStepConfigEditorProps) {
  const properties = schema.properties ?? {};
  const required = new Set(schema.required ?? []);

  function updateField(name: string, fieldValue: unknown) {
    onChange({
      ...value,
      [name]: fieldValue,
    });
  }

  return (
    <div className="space-y-4">
      {Object.entries(properties).map(([name, fieldSchema]) => {
        const currentValue =
          value[name] ?? getInitialValue(fieldSchema);

        return (
          <SchemaField
            key={name}
            name={name}
            schema={fieldSchema}
            value={currentValue}
            required={required.has(name)}
            availableColumns={availableColumns}
            onChange={(fieldValue) => updateField(name, fieldValue)}
          />
        );
      })}
    </div>
  );
}

type SchemaFieldProps = {
  name: string;
  schema: JsonSchemaProperty;
  value: unknown;
  required: boolean;
  availableColumns: string[];
  onChange: (value: unknown) => void;
};

function SchemaField({
  name,
  schema,
  value,
  required,
  availableColumns,
  onChange,
}: SchemaFieldProps) {
  const label = schema.title ?? name;
  const editor = schema["crucible:editor"];

  if (editor === "column-multiselect") {
    const selected = Array.isArray(value) ? value.map(String) : [];

    return (
      <div className="space-y-2">
        <FieldLabel label={label} required={required} description={schema.description} />

        <div className="flex flex-wrap gap-2">
          {availableColumns.map((column) => {
            const checked = selected.includes(column);

            return (
              <Button
                key={column}
                type="button"
                variant={checked ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  if (checked) {
                    onChange(selected.filter((item) => item !== column));
                  } else {
                    onChange([...selected, column]);
                  }
                }}
              >
                {column}
              </Button>
            );
          })}
        </div>
      </div>
    );
  }

  if (editor === "column-select") {
    return (
      <div className="space-y-2">
        <FieldLabel label={label} required={required} description={schema.description} />

        <select
          className="w-full rounded-md border px-3 py-2 text-sm"
          value={typeof value === "string" ? value : ""}
          onChange={(event) => onChange(event.target.value)}
        >
          <option value="">Select column...</option>
          {availableColumns.map((column) => (
            <option key={column} value={column}>
              {column}
            </option>
          ))}
        </select>
      </div>
    );
  }

  if (schema.enum) {
    return (
      <div className="space-y-2">
        <FieldLabel label={label} required={required} description={schema.description} />

        <select
          className="w-full rounded-md border px-3 py-2 text-sm"
          value={typeof value === "string" ? value : ""}
          onChange={(event) => onChange(event.target.value)}
        >
          <option value="">Select...</option>
          {schema.enum.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>
    );
  }

  if (schema.type === "boolean") {
    return (
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={Boolean(value)}
          onChange={(event) => onChange(event.target.checked)}
        />
        {label}
        {required ? " *" : ""}
      </label>
    );
  }

  if (schema.type === "integer" || schema.type === "number") {
    return (
      <div className="space-y-2">
        <FieldLabel label={label} required={required} description={schema.description} />

        <Input
          type="number"
          value={typeof value === "number" ? value : ""}
          onChange={(event) => {
            const raw = event.target.value;
            onChange(raw === "" ? null : Number(raw));
          }}
        />
      </div>
    );
  }

  if (schema.type === "array") {
    const arrayValue = Array.isArray(value) ? value : [];

    return (
      <div className="space-y-2">
        <FieldLabel label={label} required={required} description={schema.description} />

        <Input
          value={arrayValue.join(", ")}
          onChange={(event) => {
            const items = event.target.value
              .split(",")
              .map((item) => item.trim())
              .filter(Boolean);

            onChange(items);
          }}
          placeholder="value1, value2, value3"
        />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <FieldLabel label={label} required={required} description={schema.description} />

      <Input
        value={typeof value === "string" ? value : ""}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function FieldLabel({
  label,
  required,
  description,
}: {
  label: string;
  required: boolean;
  description?: string;
}) {
  return (
    <div>
      <div className="text-sm font-medium">
        {label}
        {required ? " *" : ""}
      </div>

      {description ? (
        <div className="text-xs text-muted-foreground">{description}</div>
      ) : null}
    </div>
  );
}
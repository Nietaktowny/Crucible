import { parse, stringify } from "yaml";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { WorkflowStep } from "@/features/workflow/types";

type StepConfigPanelProps = {
  step: WorkflowStep | null;
  onUpdateParameters: (field: string, value: unknown) => void;
  onUpdateMetadata: (field: "name" | "description", value: string) => void;
  onRemoveStep: () => void;
};

function isComplexValue(value: unknown) {
  return typeof value === "object" && value !== null;
}

function parsePrimitiveValue(value: string, previousValue: unknown): unknown {
  if (typeof previousValue === "number") {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? value : parsed;
  }

  if (typeof previousValue === "boolean") {
    return value === "true";
  }

  if (previousValue === null) {
    if (value === "") return null;
    if (value === "null") return null;
    if (value === "true") return true;
    if (value === "false") return false;

    const parsed = Number(value);

    if (!Number.isNaN(parsed) && value.trim() !== "") {
      return parsed;
    }

    return value;
  }

  return value;
}

function ConfigValueEditor({
  field,
  value,
  onChange,
}: {
  field: string;
  value: unknown;
  onChange: (field: string, value: unknown) => void;
}) {
  if (isComplexValue(value)) {
    return (
      <textarea
        className="min-h-32 w-full rounded-md border bg-background px-3 py-2 font-mono text-xs text-foreground"
        value={stringify(value, {
          indent: 2,
          lineWidth: 0,
          nullStr: "null",
        })}
        onChange={(event) => {
          try {
            onChange(field, parse(event.target.value));
          } catch {
            // Invalid YAML while typing.
          }
        }}
      />
    );
  }

  if (typeof value === "boolean") {
    return (
      <select
        className="h-10 w-full rounded-md border bg-background px-3 text-sm text-foreground"
        value={String(value)}
        onChange={(event) => onChange(field, event.target.value === "true")}
      >
        <option value="true">true</option>
        <option value="false">false</option>
      </select>
    );
  }

  return (
    <Input
      value={String(value ?? "")}
      onChange={(event) =>
        onChange(field, parsePrimitiveValue(event.target.value, value))
      }
    />
  );
}

export default function StepConfigPanel({
  step,
  onUpdateParameters,
  onUpdateMetadata,
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
          <div className="text-xs font-medium text-muted-foreground">
            Step key
          </div>

          <Input value={step.key} disabled />
        </div>

        <div className="space-y-2">
          <div className="text-xs font-medium text-muted-foreground">
            Custom name
          </div>

          <Input
            value={step.name}
            onChange={(event) => onUpdateMetadata("name", event.target.value)}
          />
        </div>

        <div className="space-y-2">
          <div className="text-xs font-medium text-muted-foreground">
            Custom description
          </div>

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
            {Object.entries(step.parameters).map(([field, value]) => (
              <div key={field} className="space-y-2">
                <div className="text-xs font-medium text-muted-foreground">
                  {field}
                </div>

                <ConfigValueEditor
                  field={field}
                  value={value}
                  onChange={onUpdateParameters}
                />
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="border-t p-4">
        <Button variant="destructive" className="w-full" onClick={onRemoveStep}>
          Remove step
        </Button>
      </div>
    </section>
  );
}
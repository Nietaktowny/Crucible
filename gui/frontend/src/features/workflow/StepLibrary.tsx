import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { stepRegistry, type StepKey } from "@/features/workflow/stepRegistry";

type StepLibraryProps = {
  onAddStep: (key: StepKey) => void;
};

export default function StepLibrary({ onAddStep }: StepLibraryProps) {
  const [search, setSearch] = useState("");

  const filteredSteps = useMemo(() => {
    const query = search.trim().toLowerCase();

    return Object.entries(stepRegistry).filter(([key, definition]) => {
      if (!query) return true;

      return (
        key.toLowerCase().includes(query) ||
        definition.label.toLowerCase().includes(query) ||
        definition.description.toLowerCase().includes(query)
      );
    }) as [StepKey, (typeof stepRegistry)[StepKey]][];
  }, [search]);

  return (
    <section className="flex min-h-0 flex-col rounded-lg border bg-card">
      <div className="border-b p-3">
        <h2 className="text-sm font-semibold">Step Library</h2>

        <Input
          className="mt-3"
          placeholder="Search steps..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </div>

      <div className="min-h-0 flex-1 space-y-2 overflow-auto p-3">
        {filteredSteps.map(([key, definition]) => (
          <Button
            key={key}
            variant="outline"
            className="h-auto w-full justify-start whitespace-normal px-3 py-2 text-left"
            onClick={() => onAddStep(key)}
          >
            <div>
              <div className="font-medium">{definition.label}</div>
              <div className="text-xs text-muted-foreground">{key}</div>
            </div>
          </Button>
        ))}
      </div>
    </section>
  );
}
import { useState } from "react";
import { stringify } from "yaml";

import { Button } from "@/components/ui/button";
import type { Workflow } from "@/features/workflow/types";

type WorkflowPreviewProps = {
  workflow: Workflow;
};

function toYamlObject(workflow: Workflow) {
  return {
    name: workflow.name,
    steps: workflow.steps.map((step) => ({
      key: step.key,
      name: step.name,
      description: step.description,
      parameters: step.parameters,
    })),
  };
}

export default function WorkflowPreview({ workflow }: WorkflowPreviewProps) {
  const [copied, setCopied] = useState(false);

  const yamlText = stringify(toYamlObject(workflow), {
    indent: 2,
    lineWidth: 0,
    nullStr: "null",
  });

  async function copyYaml() {
    await navigator.clipboard.writeText(yamlText);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-end border-b px-4 py-2">
        <Button size="sm" variant="outline" onClick={copyYaml}>
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>

      <pre className="min-h-0 flex-1 overflow-auto bg-background p-4 text-sm text-foreground">
        <code>{yamlText}</code>
      </pre>
    </div>
  );
}
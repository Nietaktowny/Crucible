import { useState } from "react";
import { Button } from "@/components/ui/button";

type ErrorPanelProps = {
  title?: string;
  message: string;
  details?: string;
  onClose?: () => void;
};

export default function ErrorPanel({
  title = "Execution failed",
  message,
  details,
  onClose,
}: ErrorPanelProps) {
  const [copied, setCopied] = useState(false);

  const textToCopy = details ? `${message}\n\n${details}` : message;

  async function copyError() {
    await navigator.clipboard.writeText(textToCopy);
    setCopied(true);

    window.setTimeout(() => {
      setCopied(false);
    }, 1500);
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 rounded-md border border-destructive/40 bg-background shadow-lg">
      <div className="flex items-center gap-3 border-b px-4 py-2">
        <div className="font-semibold text-destructive">{title}</div>

        <div className="ml-auto flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={copyError}>
            {copied ? "Copied" : "Copy"}
          </Button>

          {onClose && (
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
          )}
        </div>
      </div>

      <div className="max-h-64 overflow-auto px-4 py-3">
        <div className="font-mono text-sm text-destructive whitespace-pre-wrap">
          {message}
        </div>

        {details && (
          <pre className="mt-3 whitespace-pre-wrap rounded bg-muted p-3 text-xs">
            {details}
          </pre>
        )}
      </div>
    </div>
  );
}
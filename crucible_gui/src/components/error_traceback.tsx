import { useState } from "react";
import { ActionIcon, Badge, Group, Stack, Text, Tooltip } from "@mantine/core";
import { IconAlertTriangle, IconCheck, IconCopy } from "@tabler/icons-react";

type ErrorTracebackProps = {
  /** Short, human summary of the failure (e.g. the step's exception message). */
  message: string;
  /** Name of the step that failed, if known. Omit for a run-level/unexpected failure. */
  stepName?: string | null;
  /** Full formatted traceback text, if the server sent one. */
  traceback?: string | null;
};

/**
 * Failure detail block for a workflow run, styled after Dagster's run-log
 * error view: a headline banner naming what failed, followed by a
 * scrollable, copyable, monospace stack trace.
 */
export function ErrorTraceback({ message, stepName, traceback }: ErrorTracebackProps) {
  const [copied, setCopied] = useState(false);

  const exceptionType = extractExceptionType(traceback);

  async function copyTraceback() {
    try {
      await navigator.clipboard.writeText(traceback ?? message);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access denied — nothing useful to do about it here.
    }
  }

  return (
    <Stack
      gap={0}
      style={{
        borderRadius: "var(--mantine-radius-md)",
        border: "1px solid rgba(224, 49, 49, 0.4)",
        background: "rgba(224, 49, 49, 0.06)",
        overflow: "hidden",
      }}
    >
      <Group justify="space-between" wrap="nowrap" p="sm" gap="xs">
        <Group gap={8} wrap="nowrap" style={{ minWidth: 0 }}>
          <IconAlertTriangle size={16} color="#e03131" style={{ flex: "none" }} />
          <Stack gap={2} style={{ minWidth: 0 }}>
            <Group gap={6} wrap="nowrap">
              <Text fw={700} size="sm" c="red.4">
                {stepName ? `Step failed: ${stepName}` : "Run failed"}
              </Text>
              {exceptionType && (
                <Badge size="xs" variant="light" color="red">
                  {exceptionType}
                </Badge>
              )}
            </Group>
            <Text size="xs" c="red.2" lineClamp={2}>
              {message}
            </Text>
          </Stack>
        </Group>

        {traceback && (
          <Tooltip label={copied ? "Copied" : "Copy traceback"}>
            <ActionIcon
              variant="subtle"
              color={copied ? "teal" : "gray"}
              onClick={() => void copyTraceback()}
            >
              {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
            </ActionIcon>
          </Tooltip>
        )}
      </Group>

      {traceback && (
        <Text
          component="pre"
          size="xs"
          ff="monospace"
          p="sm"
          style={{
            margin: 0,
            maxHeight: 320,
            overflow: "auto",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            color: "#e8a8a8",
            background: "#150a0a",
            borderTop: "1px solid rgba(224, 49, 49, 0.25)",
          }}
        >
          {traceback}
        </Text>
      )}
    </Stack>
  );
}

function extractExceptionType(traceback: string | null | undefined): string | null {
  if (!traceback) {
    return null;
  }

  const lines = traceback.trim().split("\n");
  const lastLine = lines[lines.length - 1] ?? "";
  const match = /^([\w.]+(?:Error|Exception|Warning)?):/.exec(lastLine);

  return match ? match[1] : null;
}

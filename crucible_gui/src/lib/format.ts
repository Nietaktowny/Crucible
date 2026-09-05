import type { WorkflowRunErrorBody } from "@/types/workflows";

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    const cause = error.cause as { message?: string } | undefined;
    return cause?.message ?? error.message;
  }

  return "Something went wrong.";
}

/**
 * Reduces a full Python traceback down to its final "ExceptionType: reason"
 * line, for use as a short headline alongside the full trace.
 */
export function getTracebackHeadline(traceback: string): string {
  const lines = traceback.trim().split("\n");
  return lines[lines.length - 1]?.trim() ?? traceback;
}

/**
 * Pulls the structured `{error, message, step_name, traceback, ...}` body
 * the server sends for a failed run out of an error thrown by
 * `CrucibleClient` (attached as `error.cause`), if present.
 */
export function getRunErrorBody(error: unknown): { message: string; step_name?: string; traceback?: string } | null {
  if (!(error instanceof Error) || typeof error.cause !== "object" || error.cause === null) {
    return null;
  }

  const cause = error.cause as Record<string, unknown>;

  if (typeof cause.message !== "string") {
    return null;
  }

  return {
    message: cause.message,
    step_name: typeof cause.step_name === "string" ? cause.step_name : undefined,
    traceback: typeof cause.traceback === "string" ? cause.traceback : undefined,
  };
}

export function formatDuration(totalSeconds: number | null | undefined): string {
  if (totalSeconds === null || totalSeconds === undefined || Number.isNaN(totalSeconds)) {
    return "—";
  }

  if (totalSeconds < 1) {
    return `${Math.round(totalSeconds * 1000)}ms`;
  }

  if (totalSeconds < 60) {
    return `${totalSeconds.toFixed(totalSeconds < 10 ? 2 : 1)}s`;
  }

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.round(totalSeconds % 60);
  return `${minutes}m ${seconds}s`;
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "—";
  }

  return new Intl.NumberFormat().format(value);
}

export function formatRelativeDate(date: Date): string {
  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.round(diffMs / 60000);

  if (diffMinutes < 1) return "just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;

  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.round(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

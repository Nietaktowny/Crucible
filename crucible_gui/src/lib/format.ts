export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    const cause = error.cause as { message?: string } | undefined;
    return cause?.message ?? error.message;
  }

  return "Something went wrong.";
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

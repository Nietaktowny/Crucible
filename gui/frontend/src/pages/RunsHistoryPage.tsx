import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { listRuns, type WorkflowRunResult } from "@/lib/crucibleApi";

function formatDate(value: string | null): string {
  if (!value) return "-";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return "-";

  return `${seconds.toFixed(3)} s`;
}

function statusLabel(status: string): string {
  return status.toUpperCase();
}

export default function RunsHistoryPage() {
  const [runs, setRuns] = useState<WorkflowRunResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadRuns() {
    setLoading(true);
    setError(null);

    try {
      const data = await listRuns();
      setRuns(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load runs history.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadRuns();
  }, []);

  return (
    <main className="flex h-full flex-col gap-4 bg-background p-6 text-foreground">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Runs history</h1>
          <p className="text-sm text-muted-foreground">
            Previously executed workflow runs stored by the backend.
          </p>
        </div>

        <Button onClick={loadRuns} disabled={loading}>
          Refresh
        </Button>
      </header>

      {error && (
        <div className="rounded-md border border-destructive p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="overflow-auto rounded-md border">
        <table className="w-full border-collapse text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Workflow</th>
              <th className="px-3 py-2 text-left font-medium">Run ID</th>
              <th className="px-3 py-2 text-left font-medium">Status</th>
              <th className="px-3 py-2 text-left font-medium">Rows</th>
              <th className="px-3 py-2 text-left font-medium">Steps</th>
              <th className="px-3 py-2 text-left font-medium">Started</th>
              <th className="px-3 py-2 text-left font-medium">Ended</th>
              <th className="px-3 py-2 text-left font-medium">Duration</th>
              <th className="px-3 py-2 text-left font-medium">Error step</th>
            </tr>
          </thead>

          <tbody>
            {loading && (
              <tr>
                <td
                  colSpan={9}
                  className="px-3 py-6 text-center text-muted-foreground"
                >
                  Loading runs...
                </td>
              </tr>
            )}

            {!loading && runs.length === 0 && (
              <tr>
                <td
                  colSpan={9}
                  className="px-3 py-6 text-center text-muted-foreground"
                >
                  No runs found.
                </td>
              </tr>
            )}

            {!loading &&
              runs.map((run) => (
                <tr key={run.run_id} className="border-t">
                  <td className="max-w-[220px] truncate px-3 py-2 font-medium">
                    {run.name ?? "-"}
                  </td>

                  <td className="max-w-[220px] truncate px-3 py-2 font-mono">
                    {run.run_id}
                  </td>

                  <td className="px-3 py-2">{statusLabel(run.status)}</td>

                  <td className="px-3 py-2">{run.row_count ?? "-"}</td>

                  <td className="px-3 py-2">
                    {run.statistics?.total_steps ?? "-"}
                  </td>

                  <td className="px-3 py-2">
                    {formatDate(run.statistics?.started_at ?? null)}
                  </td>

                  <td className="px-3 py-2">
                    {formatDate(run.statistics?.ended_at ?? null)}
                  </td>

                  <td className="px-3 py-2">
                    {formatDuration(run.statistics?.total_time)}
                  </td>

                  <td className="px-3 py-2">
                    {run.error ? run.error.step_name : "-"}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
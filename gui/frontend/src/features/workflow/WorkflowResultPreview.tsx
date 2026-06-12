import type { PreviewRow } from "@/lib/crucibleApi";

type WorkflowResultPreviewProps = {
  preview: PreviewRow[] | null;
  rowCount: number | null;
};

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}

export default function WorkflowResultPreview({
  preview,
  rowCount,
}: WorkflowResultPreviewProps) {
  if (!preview || preview.length === 0) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        No preview available. Run workflow first.
      </div>
    );
  }

  const columns = Object.keys(preview[0] ?? {});

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="border-b px-4 py-2 text-sm text-muted-foreground">
        Row count: {rowCount ?? "unknown"} · Preview rows: {preview.length}
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 bg-card">
            <tr>
              {columns.map((column) => (
                <th
                  key={column}
                  className="whitespace-nowrap border-b px-3 py-2 text-left font-medium"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {preview.map((row, rowIndex) => (
              <tr key={rowIndex} className="border-b">
                {columns.map((column) => (
                  <td
                    key={column}
                    className="max-w-[240px] truncate px-3 py-2"
                    title={formatValue(row[column])}
                  >
                    {formatValue(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
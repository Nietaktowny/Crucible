import { Text } from "@mantine/core";

type TableRow = Record<string, unknown>;

type DynamicTableProps = {
  data: TableRow[];
};

export function DynamicTable({ data }: DynamicTableProps) {
  if (data.length === 0) {
    return (
      <Text size="sm" c="dimmed" py="md" ta="center">
        No data
      </Text>
    );
  }

  const columns = Array.from(
    new Set(data.flatMap((row) => Object.keys(row)))
  );

  return (
    <div className="table-scroll-container">
      <table className="dynamic-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>

        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column) => (
                <td key={column}>{String(row[column] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

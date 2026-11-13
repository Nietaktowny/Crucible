import { useMemo, useState } from "react";
import { ActionIcon, Checkbox, Group, Menu, Stack, Text } from "@mantine/core";
import { IconChevronDown, IconFilter } from "@tabler/icons-react";
import { tableFeatures, useTable, type ColumnDef } from "@tanstack/react-table";

import { displayValue } from "./model";

type Row = Record<string, unknown>;
const features = tableFeatures({});

type DataTableProps = {
  data: Row[];
  schema: Record<string, string>;
  columnOrder?: string[];
  selectedColumns: string[];
  onSelectColumns: (columns: string[]) => void;
  onAction: (key: string, columns: string[], value?: unknown) => void;
  onFilters: (column: string) => void;
  filterColumns: string[];
  disabled: boolean;
};

export function DataTable({
  data,
  schema,
  columnOrder,
  selectedColumns,
  onSelectColumns,
  onAction,
  onFilters,
  filterColumns,
  disabled,
}: DataTableProps) {
  const columns = useMemo<ColumnDef<typeof features, Row>[]>(
    () =>
      (columnOrder ?? Object.keys(schema)).map((column) => ({
        id: column,
        accessorFn: (row) => row[column],
        header: column,
      })),
    [schema, columnOrder],
  );
  const table = useTable({ features, data, columns });
  const [activeCell, setActiveCell] = useState<{
    id: string;
    data: Row[];
  } | null>(null);

  return (
    <div className="workflow-data-scroll">
      <table className="dynamic-table workflow-data-table">
        <thead>
          {table.getHeaderGroups().map((group) => (
            <tr key={group.id}>
              <th aria-label="Row number">#</th>
              {group.headers.map((header) => {
                const column = header.column.id;
                return (
                  <th key={header.id}>
                    <Group gap={6} wrap="nowrap">
                      <Checkbox
                        size="xs"
                        aria-label={`Select column ${column}`}
                        checked={selectedColumns.includes(column)}
                        onChange={(event) =>
                          onSelectColumns(
                            event.currentTarget.checked
                              ? [...selectedColumns, column]
                              : selectedColumns.filter(
                                  (name) => name !== column,
                                ),
                          )
                        }
                      />
                      <Stack gap={0} style={{ flex: 1 }}>
                        <Text size="sm" fw={600}>
                          {column}
                        </Text>
                        <Text size="10px" c="dimmed">
                          {schema[column]}
                        </Text>
                      </Stack>
                      {filterColumns.includes(column) && (
                        <ActionIcon
                          size="xs"
                          variant="subtle"
                          aria-label={`Applied filters for ${column}`}
                          onClick={() => onFilters(column)}
                        >
                          <IconFilter size={13} />
                        </ActionIcon>
                      )}
                      <Menu withinPortal position="bottom-start">
                        <Menu.Target>
                          <ActionIcon
                            size="sm"
                            variant="subtle"
                            disabled={disabled}
                            aria-label={`Actions for ${column}`}
                          >
                            <IconChevronDown size={14} />
                          </ActionIcon>
                        </Menu.Target>
                        <Menu.Dropdown>
                          <Menu.Item
                            onClick={() => onAction("filter_rows", [column])}
                          >
                            Filter rows…
                          </Menu.Item>
                          <Menu.Item
                            onClick={() => onAction("sort_asc", [column])}
                          >
                            Sort ascending…
                          </Menu.Item>
                          <Menu.Item
                            onClick={() => onAction("sort_desc", [column])}
                          >
                            Sort descending…
                          </Menu.Item>
                          <Menu.Divider />
                          <Menu.Item
                            onClick={() => onAction("rename_columns", [column])}
                          >
                            Rename…
                          </Menu.Item>
                          <Menu.Item
                            onClick={() =>
                              onAction("change_column_type", [column])
                            }
                          >
                            Change type…
                          </Menu.Item>
                          <Menu.Item
                            onClick={() => onAction("drop_columns", [column])}
                          >
                            Remove column…
                          </Menu.Item>
                          <Menu.Item
                            onClick={() => onAction("select_columns", [column])}
                          >
                            Keep only this column…
                          </Menu.Item>
                          <Menu.Divider />
                          <Menu.Item
                            onClick={() => onAction("replace_values", [column])}
                          >
                            Replace values…
                          </Menu.Item>
                          <Menu.Item
                            onClick={() => onAction("fill_nulls", [column])}
                          >
                            Fill nulls…
                          </Menu.Item>
                          <Menu.Item
                            onClick={() => onAction("fill_down", [column])}
                          >
                            Fill down…
                          </Menu.Item>
                          <Menu.Item
                            onClick={() => onAction("drop_nulls", [column])}
                          >
                            Remove nulls…
                          </Menu.Item>
                          <Menu.Item
                            onClick={() => onAction("split_column", [column])}
                          >
                            Split column…
                          </Menu.Item>
                        </Menu.Dropdown>
                      </Menu>
                    </Group>
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row, index) => (
            <tr key={row.id}>
              <td className="workflow-row-number">{index + 1}</td>
              {row.getAllCells().map((cell) => {
                const button = (
                  <button
                    type="button"
                    className="workflow-cell"
                    disabled={disabled}
                    aria-label={`${cell.column.id}: ${displayValue(cell.getValue())}`}
                    aria-haspopup="menu"
                    onClick={() => setActiveCell({ id: cell.id, data })}
                  >
                    {displayValue(cell.getValue())}
                  </button>
                );
                // Mount a popup only for the active cell, rather than thousands
                // of closed popovers for an ordinary preview.
                return (
                  <td key={cell.id}>
                    {!disabled &&
                    activeCell?.id === cell.id &&
                    activeCell.data === data ? (
                      <Menu
                        opened
                        onChange={(opened) => {
                          if (!opened) setActiveCell(null);
                        }}
                        withinPortal
                        position="bottom-start"
                      >
                        <Menu.Target>{button}</Menu.Target>
                        <Menu.Dropdown>
                          <Menu.Item
                            onClick={() =>
                              onAction(
                                "keep_value",
                                [cell.column.id],
                                cell.getValue(),
                              )
                            }
                          >
                            Keep this value…
                          </Menu.Item>
                          <Menu.Item
                            onClick={() =>
                              onAction(
                                "exclude_value",
                                [cell.column.id],
                                cell.getValue(),
                              )
                            }
                          >
                            Exclude this value…
                          </Menu.Item>
                          <Menu.Item
                            onClick={() =>
                              onAction(
                                "replace_values",
                                [cell.column.id],
                                cell.getValue(),
                              )
                            }
                          >
                            Replace this value…
                          </Menu.Item>
                        </Menu.Dropdown>
                      </Menu>
                    ) : (
                      button
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length === 0 && (
        <Text p="xl" ta="center" c="dimmed">
          No preview rows returned.
        </Text>
      )}
    </div>
  );
}

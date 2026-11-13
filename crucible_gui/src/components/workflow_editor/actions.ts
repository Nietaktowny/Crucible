import type { StepConfig } from "@/types/workflows";
import type { StepSchema } from "@/types/step_schema";
import { getInitialParameters } from "@/components/step_editor/model";
import { valueCondition } from "./model";

export const transformationGroups = [
  {
    label: "Columns",
    actions: [
      ["rename_columns", "Rename"],
      ["change_column_type", "Change type"],
      ["select_columns", "Keep columns"],
      ["drop_columns", "Remove columns"],
      ["reorder_columns", "Reorder columns"],
      ["create_column", "Calculated column"],
    ],
  },
  {
    label: "Rows",
    actions: [
      ["filter_rows", "Filter rows"],
      ["sort_rows", "Sort rows"],
      ["head_rows", "Keep top rows"],
      ["tail_rows", "Keep bottom rows"],
      ["remove_duplicates", "Remove duplicates"],
      ["drop_nulls", "Remove nulls"],
    ],
  },
  {
    label: "Transform",
    actions: [
      ["replace_values", "Replace values"],
      ["fill_nulls", "Fill nulls"],
      ["fill_down", "Fill down"],
      ["split_column", "Split column"],
      ["group_by", "Group by"],
      ["pivot", "Pivot"],
      ["unpivot", "Unpivot"],
      ["parse_datetime", "Parse date/time"],
      ["date_range_filter", "Date range filter"],
      ["date_period_filter", "Relative date filter"],
    ],
  },
];

export function createActionStep(
  action: string,
  columns: string[],
  schemas: StepSchema[],
  frameSchema: Record<string, string>,
  value?: unknown,
): StepConfig {
  const key =
    action === "keep_value" || action === "exclude_value"
      ? "filter_rows"
      : action.startsWith("sort_") && action !== "sort_rows"
        ? "sort_rows"
        : action === "head_rows" || action === "tail_rows"
          ? "limit_rows"
          : action;
  const schema = schemas.find((item) => item.key === key);
  const parameters = schema ? getInitialParameters(schema) : {};
  const first = columns[0];
  if (
    [
      "select_columns",
      "drop_columns",
      "fill_down",
      "drop_nulls",
      "fill_nulls",
      "remove_duplicates",
    ].includes(key) &&
    columns.length
  )
    parameters.columns = columns;
  if (key === "reorder_columns")
    parameters.columns = [
      ...columns,
      ...Object.keys(frameSchema).filter((column) => !columns.includes(column)),
    ];
  if (key === "sort_rows")
    parameters.columns = columns.map((name) => ({
      name,
      direction: action === "sort_desc" ? "desc" : "asc",
    }));
  if (key === "rename_columns" && first)
    parameters.mapping = { [first]: first };
  if (key === "change_column_type")
    parameters.column_types = Object.fromEntries(
      columns.map((column) => [column, "string"]),
    );
  if (
    [
      "split_column",
      "replace_values",
      "parse_datetime",
      "date_range_filter",
      "date_period_filter",
    ].includes(key) &&
    first
  )
    parameters.column = first;
  if (key === "replace_values" && value !== undefined) parameters.old = value;
  if (key === "group_by") parameters.by = columns;
  if (key === "pivot") parameters.on = columns;
  if (key === "unpivot") {
    parameters.on = columns;
    parameters.index = Object.keys(frameSchema).filter(
      (column) => !columns.includes(column),
    );
  }
  if (key === "limit_rows") {
    parameters.mode = action === "tail_rows" ? "tail" : "head";
    parameters.limit = 10;
  }
  if (key === "filter_rows" && first && action !== "filter_rows")
    parameters.condition = valueCondition(
      first,
      value,
      frameSchema[first],
      action === "exclude_value",
    );
  return {
    step_id: crypto.randomUUID(),
    key,
    name: key === "filter_rows" ? "Filter" : (schema?.default_name ?? key),
    description: schema?.default_description ?? "",
    parameters,
  };
}

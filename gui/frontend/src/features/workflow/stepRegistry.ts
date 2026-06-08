export type StepConfig = Record<string, unknown>;

export type StepDefinition = {
  label: string;
  description: string;
  defaultConfig: StepConfig;
};

export const stepRegistry = {
  read_csv: {
    label: "Read CSV File",
    description: "Read data from a CSV file",
    defaultConfig: {
      path: "",
      separator: ",",
      infer_types: false,
      context_store: false,
      context_key: "",
    },
  },

  write_csv: {
    label: "Write CSV File",
    description: "Write data to a CSV file",
    defaultConfig: {
      path: "",
      separator: ",",
    },
  },

  read_excel: {
    label: "Read Excel File",
    description: "Read data from an Excel workbook.",
    defaultConfig: {
      path: "",
      sheet: null,
      context_store: false,
      context_key: null,
    },
  },

  write_excel: {
    label: "Write Excel File",
    description: "Write data to an Excel workbook.",
    defaultConfig: {
      path: "",
      sheet: null,
    },
  },

  read_folder_csv: {
    label: "Read CSV Folder",
    description: "Read and concatenate CSV files from a folder.",
    defaultConfig: {
      path: "",
      pattern: "*.csv",
      separator: ",",
      infer_types: false,
      recursive: false,
      add_source_file: true,
      source_column: "source_file",
      context_store: false,
      context_key: "",
    },
  },

  read_folder_excel: {
    label: "Read Excel Folder",
    description: "Read and concatenate Excel files from a folder.",
    defaultConfig: {
      path: "",
      pattern: "*.xlsx",
      sheet: null,
      recursive: false,
      add_source_file: true,
      source_column: "source_file",
      add_source_path: false,
      source_path_column: "source_path",
      context_store: false,
      context_key: null,
    },
  },

  select_columns: {
    label: "Select Columns",
    description: "Select a subset of columns from the data.",
    defaultConfig: {
      columns: [],
    },
  },

  rename_columns: {
    label: "Rename Columns",
    description: "Rename columns based on a provided mapping.",
    defaultConfig: {
      mapping: {},
    },
  },

  reorder_columns: {
    label: "Reorder Columns",
    description: "Reorder columns based on a specified list of column names.",
    defaultConfig: {
      columns: [],
    },
  },

  change_column_type: {
    label: "Change Column Type",
    description: "Change the data type of one or more columns.",
    defaultConfig: {
      column_types: {},
    },
  },

  filter_rows: {
    label: "Filter Rows",
    description: "Filter rows based on a declarative condition.",
    defaultConfig: {
      condition: {},
    },
  },

  sort_rows: {
    label: "Sort Rows",
    description: "Sort rows based on specified columns and sort directions.",
    defaultConfig: {
      columns: [{ name: "", direction: "asc" }],
    },
  },

  limit_rows: {
    label: "Limit rows",
    description: "Limit rows to first or last n rows",
    defaultConfig: {
      limit: 10,
      mode: "head",
    },
  },

  remove_duplicates: {
    label: "Remove Duplicates",
    description: "Remove duplicate rows.",
    defaultConfig: {
      columns: null,
      keep: "first",
    },
  },

  drop_nulls: {
    label: "Drop Nulls",
    description: "Remove rows containing null values.",
    defaultConfig: {
      columns: null,
    },
  },

  fill_nulls: {
    label: "Fill Nulls",
    description: "Replace null values with a specified value.",
    defaultConfig: {
      columns: [],
      value: null,
    },
  },

  fill_down: {
    label: "Fill Down",
    description: "Fill null values with the previous non-null value.",
    defaultConfig: {
      columns: [],
    },
  },

  replace_values: {
    label: "Replace Values",
    description: "Replace values in a column.",
    defaultConfig: {
      column: "",
      old: null,
      new: null,
      mapping: null,
    },
  },

  split_column: {
    label: "Split Column",
    description: "Split a text column into multiple columns.",
    defaultConfig: {
      column: "",
      delimiter: "",
      into: [],
      max_splits: null,
      drop_original: false,
    },
  },

  regex_extract: {
    label: "Regex Extract",
    description: "Extract text from a column using a regular expression.",
    defaultConfig: {
      column: "",
      pattern: "",
      output_column: "",
      group_index: 1,
    },
  },

  create_column: {
    label: "Create Column",
    description: "Create a new column from a declarative expression.",
    defaultConfig: {
      name: "",
      expr: {},
    },
  },

  group_by: {
    label: "Group By",
    description: "Group rows and calculate aggregations.",
    defaultConfig: {
      by: [],
      aggregations: [{ column: "", function: "sum", alias: null }],
    },
  },

  join: {
    label: "Join",
    description: "Join two datasets",
    defaultConfig: {
      left_on: "",
      right_on: "",
      how: "left",
    },
  },

  concat: {
    label: "Concatenate rows",
    description: "Append rows from multiple sources",
    defaultConfig: {
      how: "vertical",
    },
  },

  pivot: {
    label: "Pivot",
    description: "Pivot the data from long to wide format.",
    defaultConfig: {
      on: [],
      index: [],
      values: [],
      aggregate_function: "first",
    },
  },

  unpivot: {
    label: "Unpivot",
    description: "Unpivot the data from wide to long format.",
    defaultConfig: {
      on: [],
      index: [],
      variable_name: "variable",
      value_name: "value",
    },
  },

  parse_datetime: {
    label: "Parse Date/Time",
    description: "Parse a text column into date, datetime, or time.",
    defaultConfig: {
      column: "",
      target_type: "date",
      format: null,
      output_column: null,
      strict: false,
    },
  },

  extract_date_time: {
    label: "Extract Date/Time",
    description: "Extract date or time from a datetime column.",
    defaultConfig: {
      column: "",
      extract: "date",
      output_column: null,
    },
  },

  extract_datetime_part: {
    label: "Extract Date/Time Part",
    description: "Extract a selected part from a date, datetime, or time column.",
    defaultConfig: {
      column: "",
      part: "year",
      output_column: null,
    },
  },

  date_diff: {
    label: "Date Difference",
    description: "Calculate difference between two date or datetime values.",
    defaultConfig: {
      start_column: null,
      end_column: null,
      start_value: null,
      end_value: null,
      unit: "days",
      output_column: "",
    },
  },

  date_add: {
    label: "Date Add",
    description: "Add or subtract duration from a date or datetime column.",
    defaultConfig: {
      column: "",
      value: 1,
      unit: "days",
      output_column: null,
    },
  },

  date_range_filter: {
    label: "Date Range Filter",
    description: "Filter rows where a date or datetime column is within a range.",
    defaultConfig: {
      column: "",
      start: "",
      end: "",
      value_type: "date",
      closed: "both",
    },
  },

  date_period_filter: {
    label: "Date Period Filter",
    description: "Filter rows belonging to the current year, month or day.",
    defaultConfig: {
      column: "",
      period: "current_month",
    },
  },
} as const satisfies Record<string, StepDefinition>;

export type StepKey = keyof typeof stepRegistry;
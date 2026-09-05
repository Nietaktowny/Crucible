import type {
  StepPropertyEditorType,
  StepPropertySchema,
  StepPropertySource,
} from "@/types/step_schema";

type FieldOverride = {
  title?: string;
  description?: string;
  editor?: StepPropertyEditorType;
  source?: StepPropertySource;
  advanced?: boolean;
};

export type StepSectionSpec = {
  title: string;
  fields: string[];
};

type StepUiSpec = {
  sections?: StepSectionSpec[];
  fields?: Record<string, FieldOverride>;
};

const sourceContextSections: StepSectionSpec[] = [
  {
    title: "Source",
    fields: ["path", "sheet", "columns"],
  },
  {
    title: "Options",
    fields: [
      "separator",
      "infer_types",
      "pattern",
      "recursive",
      "add_source_file",
      "source_column",
      "add_source_path",
      "source_path_column",
    ],
  },
  {
    title: "Context store",
    fields: ["context_store", "context_key"],
  },
];

/**
 * Presentation-only overrides. Domain shape, required fields and defaults stay
 * owned by the Pydantic/JSON Schema contract.
 */
const stepUiSpecs: Record<string, StepUiSpec> = {
  select_columns: {
    fields: {
      columns: { editor: "column-multiselect" },
    },
  },
  change_column_type: {
    fields: {
      column_types: {
        title: "Column types",
        editor: "mapping-builder",
      },
    },
  },
  filter_rows: {
    fields: {
      condition: { editor: "condition-builder" },
    },
  },
  rename_columns: {
    fields: {
      mapping: {
        title: "Rename pairs",
        editor: "mapping-builder",
      },
    },
  },
  sort_rows: {
    fields: {
      columns: {
        title: "Sort priority",
        editor: "list-builder",
      },
    },
  },
  reorder_columns: {
    fields: {
      columns: { editor: "list-builder" },
    },
  },
  pivot: {},
  unpivot: {
    fields: {
      on: {
        editor: "column-multiselect",
        source: "input-schema",
      },
      index: {
        editor: "column-multiselect",
        source: "input-schema",
      },
    },
  },
  read_csv: { sections: sourceContextSections },
  write_csv: {
    sections: [
      { title: "Output", fields: ["path"] },
      { title: "Options", fields: ["separator"] },
    ],
    fields: {
      path: { editor: "file-picker" },
    },
  },
  read_excel: {
    sections: sourceContextSections,
    fields: {
      sheet: { editor: "select", source: "sheets" },
    },
  },
  write_excel: {
    sections: [
      { title: "Output", fields: ["path", "sheet"] },
      { title: "Options", fields: ["table_style"] },
    ],
    fields: {
      path: { editor: "file-picker" },
    },
  },
  join: {
    sections: [
      { title: "Join type", fields: ["how"] },
      { title: "Join keys", fields: ["left_on", "right_on"] },
    ],
  },
  limit_rows: {},
  concat: {},
  group_by: {
    sections: [
      { title: "Group keys", fields: ["by"] },
      { title: "Aggregations", fields: ["aggregations"] },
    ],
    fields: {
      by: {
        editor: "column-multiselect",
        source: "input-schema",
      },
    },
  },
  remove_duplicates: {},
  replace_values: {
    sections: [
      { title: "Column", fields: ["column"] },
      {
        title: "Replacement",
        fields: ["old", "new", "mapping"],
      },
    ],
  },
  create_column: {
    fields: {
      expr: { editor: "expression-builder" },
    },
  },
  drop_nulls: {},
  fill_down: {},
  read_folder_csv: { sections: sourceContextSections },
  read_folder_excel: { sections: sourceContextSections },
  fill_nulls: {
    fields: {
      value: { editor: "value-editor" },
    },
  },
  regex_extract: {},
  split_column: {
    fields: {
      into: { editor: "list-builder" },
    },
  },
  parse_datetime: {},
  extract_date_time: {},
  extract_datetime_part: {},
  date_diff: {
    sections: [
      {
        title: "Start and end",
        fields: [
          "start_column",
          "start_value",
          "end_column",
          "end_value",
        ],
      },
      { title: "Result", fields: ["unit", "output_column"] },
    ],
  },
  date_add: {},
  date_range_filter: {},
  date_period_filter: {},
  drop_columns: {},
  __inspect_frame: {},
};

export function applyStepFieldOverride(
  stepKey: string,
  field: StepPropertySchema,
): StepPropertySchema {
  const override = stepUiSpecs[stepKey]?.fields?.[field.key];

  return override === undefined
    ? field
    : { ...field, ...override };
}

export function getStepSections(
  stepKey: string,
  fields: StepPropertySchema[],
): StepSectionSpec[] {
  const configured = stepUiSpecs[stepKey]?.sections;

  if (configured === undefined) {
    const regular = fields
      .filter((field) => !field.advanced)
      .map((field) => field.key);
    const advanced = fields
      .filter((field) => field.advanced)
      .map((field) => field.key);

    return [
      { title: "Configuration", fields: regular },
      ...(advanced.length > 0
        ? [{ title: "Advanced", fields: advanced }]
        : []),
    ];
  }

  const assigned = new Set(
    configured.flatMap((section) => section.fields),
  );
  const remaining = fields
    .filter((field) => !assigned.has(field.key))
    .map((field) => field.key);

  return [
    ...configured,
    ...(remaining.length > 0
      ? [{ title: "Additional options", fields: remaining }]
      : []),
  ];
}

export function isStepFieldVisible(
  stepKey: string,
  fieldKey: string,
  parameters: Record<string, unknown>,
): boolean {
  if (
    fieldKey === "context_key" &&
    parameters.context_store !== true
  ) {
    return false;
  }

  if (
    fieldKey === "source_column" &&
    parameters.add_source_file === false
  ) {
    return false;
  }

  if (
    fieldKey === "source_path_column" &&
    parameters.add_source_path !== true
  ) {
    return false;
  }

  if (
    stepKey === "join" &&
    (fieldKey === "left_on" || fieldKey === "right_on") &&
    parameters.how === "cross"
  ) {
    return false;
  }

  return true;
}

export type StepPropertyEditorType =
  | "text"
  | "number"
  | "checkbox"
  | "select"
  | "column-select"
  | "column-multiselect"
  | "file-picker"
  | "folder-picker"
  | "expression-builder"
  | "condition-builder"
  | "date-picker"
  | "datetime-picker"
  | "mapping-builder"
  | "list-builder"
  | "object-editor"
  | "value-editor";

export type StepPropertySource =
  | "input-schema"
  | "left-schema"
  | "right-schema"
  | "context-store"
  | "filesystem"
  | "enum"
  | "static"
  | "sheets";

export type StepPropertyRole =
  | "input-column"
  | "output-column"
  | "group-key"
  | "aggregation-column"
  | "sort-column"
  | "join-left-key"
  | "join-right-key";

export interface StepPropertyMappingSchema {
  key: StepPropertySchema;
  value: StepPropertySchema;
}

/**
 * Recursive, UI-oriented representation of a JSON Schema property.
 *
 * Keeping the nested shape is important: list item fields, mappings and
 * discriminated unions cannot be reconstructed after a schema is flattened.
 */
export interface StepPropertySchema {
  key: string;
  title: string;
  description: string;
  help: string | null;
  editor: StepPropertyEditorType;
  source: StepPropertySource;
  role: StepPropertyRole | null;
  enum: string[] | null;
  hidden: boolean;
  advanced: boolean;
  type: string;
  format: string | null;
  required: boolean;
  nullable: boolean;
  hasDefault: boolean;
  default: unknown;
  constValue: unknown;
  properties: StepPropertySchema[];
  items: StepPropertySchema | null;
  alternatives: StepPropertySchema[];
  mapping: StepPropertyMappingSchema | null;
}

export interface StepSchema {
  key: string;
  default_name: string;
  default_description: string;
  required: string[];
  properties: StepPropertySchema[];
}

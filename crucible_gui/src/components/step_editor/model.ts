import type {
  StepPropertySchema,
  StepSchema,
} from "@/types/step_schema";

export type ParameterPath = Array<string | number>;

export type StepEditorContext = {
  stepKey: string;
  parameters: Record<string, unknown>;
  inputColumns: string[];
  leftColumns: string[];
  rightColumns: string[];
  loadSheets: (path: string) => Promise<string[]>;
};

export type StepFieldChange = (
  path: ParameterPath,
  value: unknown,
) => void;

export function setValueAtPath(
  root: Record<string, unknown>,
  path: ParameterPath,
  value: unknown,
): Record<string, unknown> {
  if (path.length === 0) {
    return root;
  }

  const update = (
    current: unknown,
    depth: number,
  ): unknown => {
    const key = path[depth];
    const isArray = Array.isArray(current);
    const copy: Record<string | number, unknown> | unknown[] =
      isArray
        ? [...current]
        : {
            ...(
              current !== null &&
              typeof current === "object"
                ? current
                : {}
            ),
          };

    if (depth === path.length - 1) {
      if (value === undefined) {
        if (Array.isArray(copy) && typeof key === "number") {
          copy.splice(key, 1);
        } else {
          delete (copy as Record<string | number, unknown>)[key];
        }
      } else {
        (copy as Record<string | number, unknown>)[key] = value;
      }

      return copy;
    }

    const nextKey = path[depth + 1];
    const existing = (
      current !== null &&
      typeof current === "object"
        ? (current as Record<string | number, unknown>)[key]
        : undefined
    );

    (copy as Record<string | number, unknown>)[key] = update(
      existing ?? (typeof nextKey === "number" ? [] : {}),
      depth + 1,
    );

    return copy;
  };

  return update(root, 0) as Record<string, unknown>;
}

export function getInitialParameters(
  schema: StepSchema,
): Record<string, unknown> {
  return Object.fromEntries(
    schema.properties
      .filter((property) => property.hasDefault)
      .map((property) => [
        property.key,
        cloneValue(property.default),
      ]),
  );
}

export function getInitialValue(
  field: StepPropertySchema,
): unknown {
  if (field.hasDefault) {
    return cloneValue(field.default);
  }

  if (field.constValue !== undefined) {
    return cloneValue(field.constValue);
  }

  switch (field.editor) {
    case "checkbox":
      return false;
    case "column-multiselect":
    case "list-builder":
      return [];
    case "mapping-builder":
    case "object-editor":
      return {};
    case "number":
      return 0;
    default:
      return "";
  }
}

export function cloneValue<T>(value: T): T {
  if (value === undefined) {
    return value;
  }

  return structuredClone(value);
}

export function isEmptyValue(value: unknown): boolean {
  return (
    value === undefined ||
    value === null ||
    value === "" ||
    (Array.isArray(value) && value.length === 0) ||
    (
      typeof value === "object" &&
      value !== null &&
      !Array.isArray(value) &&
      Object.keys(value).length === 0
    )
  );
}

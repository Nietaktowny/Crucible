import { describe, expect, it } from "vitest";

import {
  cloneValue,
  getInitialParameters,
  getInitialValue,
  isEmptyValue,
  setValueAtPath,
} from "./model";
import type { StepPropertySchema, StepSchema } from "@/types/step_schema";

function makeProperty(overrides: Partial<StepPropertySchema>): StepPropertySchema {
  return {
    key: "field",
    title: "Field",
    description: "",
    help: null,
    editor: "text",
    source: "static",
    role: null,
    enum: null,
    hidden: false,
    advanced: false,
    type: "string",
    format: null,
    required: false,
    nullable: false,
    hasDefault: false,
    default: undefined,
    constValue: undefined,
    properties: [],
    items: null,
    alternatives: [],
    mapping: null,
    ...overrides,
  };
}

describe("setValueAtPath", () => {
  it("sets a top-level key", () => {
    const result = setValueAtPath({ a: 1 }, ["b"], 2);
    expect(result).toEqual({ a: 1, b: 2 });
  });

  it("sets a nested key, creating intermediate objects", () => {
    const result = setValueAtPath({}, ["a", "b"], "value");
    expect(result).toEqual({ a: { b: "value" } });
  });

  it("creates an array when the next path segment is a number", () => {
    const result = setValueAtPath({}, ["items", 0], "first");
    expect(result).toEqual({ items: ["first"] });
  });

  it("removes a key when the value is undefined", () => {
    const result = setValueAtPath({ a: 1, b: 2 }, ["a"], undefined);
    expect(result).toEqual({ b: 2 });
  });

  it("removes an array element when the value is undefined", () => {
    const result = setValueAtPath({ items: ["a", "b", "c"] }, ["items", 1], undefined);
    expect(result).toEqual({ items: ["a", "c"] });
  });

  it("does not mutate the original object", () => {
    const original = { a: { b: 1 } };
    setValueAtPath(original, ["a", "b"], 2);
    expect(original).toEqual({ a: { b: 1 } });
  });

  it("returns the root unchanged when the path is empty", () => {
    const original = { a: 1 };
    expect(setValueAtPath(original, [], 99)).toBe(original);
  });
});

describe("getInitialValue", () => {
  it("uses the field's default when present", () => {
    const field = makeProperty({ hasDefault: true, default: "hello" });
    expect(getInitialValue(field)).toBe("hello");
  });

  it("uses the const value when there is no default", () => {
    const field = makeProperty({ constValue: "fixed" });
    expect(getInitialValue(field)).toBe("fixed");
  });

  it("falls back to false for checkboxes", () => {
    expect(getInitialValue(makeProperty({ editor: "checkbox" }))).toBe(false);
  });

  it("falls back to an empty array for multi-value editors", () => {
    expect(getInitialValue(makeProperty({ editor: "column-multiselect" }))).toEqual([]);
    expect(getInitialValue(makeProperty({ editor: "list-builder" }))).toEqual([]);
  });

  it("falls back to an empty object for mapping/object editors", () => {
    expect(getInitialValue(makeProperty({ editor: "mapping-builder" }))).toEqual({});
    expect(getInitialValue(makeProperty({ editor: "object-editor" }))).toEqual({});
  });

  it("falls back to zero for numbers", () => {
    expect(getInitialValue(makeProperty({ editor: "number" }))).toBe(0);
  });

  it("falls back to an empty string for anything else", () => {
    expect(getInitialValue(makeProperty({ editor: "text" }))).toBe("");
  });
});

describe("getInitialParameters", () => {
  it("only includes properties that have a default", () => {
    const schema: StepSchema = {
      key: "example",
      default_name: "Example",
      default_description: "",
      required: [],
      properties: [
        makeProperty({ key: "with_default", hasDefault: true, default: 42 }),
        makeProperty({ key: "without_default", hasDefault: false }),
      ],
    };

    expect(getInitialParameters(schema)).toEqual({ with_default: 42 });
  });

  it("deep-clones default values so parameters don't share references", () => {
    const defaultArray = [1, 2, 3];
    const schema: StepSchema = {
      key: "example",
      default_name: "Example",
      default_description: "",
      required: [],
      properties: [makeProperty({ key: "columns", hasDefault: true, default: defaultArray })],
    };

    const params = getInitialParameters(schema);
    expect(params.columns).toEqual(defaultArray);
    expect(params.columns).not.toBe(defaultArray);
  });
});

describe("cloneValue", () => {
  it("passes through undefined instead of throwing", () => {
    expect(cloneValue(undefined)).toBeUndefined();
  });

  it("deep-clones objects and arrays", () => {
    const original = { nested: [1, { two: 2 }] };
    const clone = cloneValue(original);
    expect(clone).toEqual(original);
    expect(clone).not.toBe(original);
  });
});

describe("isEmptyValue", () => {
  it.each([undefined, null, "", [], {}])("treats %j as empty", (value) => {
    expect(isEmptyValue(value)).toBe(true);
  });

  it.each([0, false, "text", [1], { a: 1 }])("treats %j as non-empty", (value) => {
    expect(isEmptyValue(value)).toBe(false);
  });
});

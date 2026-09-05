import { describe, expect, it } from "vitest";

import { stepSchemaParser, type RawStepSchema } from "./step_schema_parser";

function schemaFor(schema: RawStepSchema["schema"]): RawStepSchema[] {
  return [
    {
      key: "example_step",
      name: "Example Step",
      description: "A step used only for parser tests.",
      schema,
    },
  ];
}

describe("stepSchemaParser", () => {
  it("carries over the step's own key/name/description", () => {
    const [parsed] = stepSchemaParser.parse(
      schemaFor({ type: "object", properties: {} }),
    );

    expect(parsed.key).toBe("example_step");
    expect(parsed.default_name).toBe("Example Step");
    expect(parsed.default_description).toBe("A step used only for parser tests.");
  });

  it("marks fields listed in the schema's required array", () => {
    const [parsed] = stepSchemaParser.parse(
      schemaFor({
        type: "object",
        required: ["path"],
        properties: {
          path: { type: "string" },
          note: { type: "string" },
        },
      }),
    );

    const path = parsed.properties.find((p) => p.key === "path")!;
    const note = parsed.properties.find((p) => p.key === "note")!;

    expect(path.required).toBe(true);
    expect(note.required).toBe(false);
  });

  it("an explicit crucible:editor annotation wins over inference", () => {
    const [parsed] = stepSchemaParser.parse(
      schemaFor({
        type: "object",
        properties: {
          sheet: {
            type: "string",
            "crucible:editor": "select",
            "crucible:source": "sheets",
          },
        },
      }),
    );

    const sheet = parsed.properties[0];
    expect(sheet.editor).toBe("select");
    expect(sheet.source).toBe("sheets");
  });

  it("infers a select editor from an enum when no editor is set", () => {
    const [parsed] = stepSchemaParser.parse(
      schemaFor({
        type: "object",
        properties: {
          function: { type: "string", enum: ["sum", "min", "max"] },
        },
      }),
    );

    const field = parsed.properties[0];
    expect(field.editor).toBe("select");
    expect(field.enum).toEqual(["sum", "min", "max"]);
  });

  it("infers a checkbox editor for boolean fields", () => {
    const [parsed] = stepSchemaParser.parse(
      schemaFor({
        type: "object",
        properties: {
          infer_types: { type: "boolean", default: false },
        },
      }),
    );

    const field = parsed.properties[0];
    expect(field.editor).toBe("checkbox");
    expect(field.hasDefault).toBe(true);
    expect(field.default).toBe(false);
  });

  it("infers a column-multiselect editor for arrays of column names", () => {
    const [parsed] = stepSchemaParser.parse(
      schemaFor({
        type: "object",
        properties: {
          columns: {
            type: "array",
            items: { type: "string", "crucible:type": "column-name" },
          },
        },
      }),
    );

    const field = parsed.properties[0];
    expect(field.editor).toBe("column-multiselect");
    expect(field.type).toBe("array");
  });

  it("forces a mapping-builder editor for dict-shaped fields", () => {
    const [parsed] = stepSchemaParser.parse(
      schemaFor({
        type: "object",
        properties: {
          column_types: {
            type: "object",
            additionalProperties: { type: "string", enum: ["string", "int64"] },
          },
        },
      }),
    );

    const field = parsed.properties[0];
    expect(field.editor).toBe("mapping-builder");
    expect(field.mapping).not.toBeNull();
    expect(field.mapping?.value.editor).toBe("select");
  });

  it("detects nullability from a nullable anyOf union", () => {
    const [parsed] = stepSchemaParser.parse(
      schemaFor({
        type: "object",
        properties: {
          sheet: { anyOf: [{ type: "string" }, { type: "null" }], default: null },
        },
      }),
    );

    const field = parsed.properties[0];
    expect(field.nullable).toBe(true);
    expect(field.type).toBe("string");
  });
});

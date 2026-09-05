import type {
  StepPropertyEditorType,
  StepPropertyRole,
  StepPropertySchema,
  StepPropertySource,
  StepSchema,
} from "@/types/step_schema";

/*
 * Generic representation of a JSON Schema node.
 *
 * The same structure is used for top-level properties, array items,
 * $defs entries, propertyNames and additionalProperties.
 */
export type RawSchemaNode = {
  $ref?: string;
  $defs?: Record<string, RawSchemaNode>;

  type?: string;
  title?: string;
  description?: string;
  format?: string;

  default?: unknown;
  const?: unknown;
  enum?: unknown[];

  required?: string[];

  properties?: Record<string, RawSchemaNode>;
  patternProperties?: Record<string, RawSchemaNode>;
  dependentSchemas?: Record<string, RawSchemaNode>;

  propertyNames?: RawSchemaNode;

  additionalProperties?:
    | boolean
    | RawSchemaNode;

  items?: RawSchemaNode;
  prefixItems?: RawSchemaNode[];
  contains?: RawSchemaNode;

  anyOf?: RawSchemaNode[];
  oneOf?: RawSchemaNode[];
  allOf?: RawSchemaNode[];

  not?: RawSchemaNode;
  if?: RawSchemaNode;
  then?: RawSchemaNode;
  else?: RawSchemaNode;

  "crucible:type"?: string;
  "crucible:editor"?: StepPropertyEditorType;
  "crucible:source"?: StepPropertySource;
  "crucible:role"?: StepPropertyRole;
  "crucible:hidden"?: boolean;
  "crucible:advanced"?: boolean;
  "crucible:help"?: string;
};

export type RawStepSchema = {
  key: string;
  name: string;
  description: string;
  schema: RawSchemaNode;
};

type RefMap = Record<string, RawSchemaNode>;

export class StepSchemaParser {
  parse(rawSchemas: RawStepSchema[]): StepSchema[] {
    return rawSchemas.map((rawSchema) =>
      this.parseStep(rawSchema),
    );
  }

  private parseStep(raw: RawStepSchema): StepSchema {
    /*
     * References are local to this individual step schema.
     *
     * Do not combine definitions from every step into one global
     * map because separate schemas can contain definitions with
     * identical names.
     */
    const refMap = this.buildRefMap(
      raw.schema.$defs ?? {},
    );

    const resolvedProperties = Object.entries(
      raw.schema.properties ?? {},
    ).map(([propertyKey, rawProperty]) => {
      const resolvedProperty = this.resolveRefs(
        rawProperty,
        refMap,
      );

      return this.parseProperty(
        propertyKey,
        resolvedProperty,
        (raw.schema.required ?? []).includes(propertyKey),
      );
    });

    return {
      key: raw.key,
      default_name: raw.name,
      default_description: raw.description,
      required: raw.schema.required ?? [],
      properties: resolvedProperties,
    };
  }

  private buildRefMap(
    definitions: Record<string, RawSchemaNode>,
  ): RefMap {
    return Object.entries(definitions).reduce<RefMap>(
      (
        map,
        [definitionName, definitionSchema],
      ) => {
        map[`#/$defs/${definitionName}`] =
          definitionSchema;

        return map;
      },
      {},
    );
  }

  /**
   * Replaces local $ref nodes with their definitions.
   *
   * Non-recursive references are fully expanded.
   * Recursive references are preserved to prevent infinite recursion.
   */
  private resolveRefs(
    node: RawSchemaNode,
    refMap: RefMap,
    activeRefs: ReadonlySet<string> = new Set(),
  ): RawSchemaNode {
    /*
     * Resolve a direct reference first.
     */
    if (node.$ref !== undefined) {
      const reference = node.$ref;
      const referencedSchema = refMap[reference];

      if (referencedSchema === undefined) {
        console.warn(
          `Cannot resolve JSON Schema reference: ${reference}`,
        );

        return this.resolveChildSchemas(
          { ...node },
          refMap,
          activeRefs,
        );
      }

      /*
       * A reference already present in the current resolution path
       * is recursive.
       *
       * Example:
       * OperationExpression -> args -> OperationExpression
       *
       * It cannot be expanded indefinitely, so preserve the $ref.
       */
      if (activeRefs.has(reference)) {
        return { ...node };
      }

      const nextActiveRefs = new Set(activeRefs);
      nextActiveRefs.add(reference);

      /*
       * JSON Schema may contain annotations next to $ref.
       * Preserve those sibling fields.
       */
      const referenceSiblings = { ...node };
      delete referenceSiblings.$ref;

      const mergedNode: RawSchemaNode = {
        ...referencedSchema,
        ...referenceSiblings,
      };

      return this.resolveRefs(
        mergedNode,
        refMap,
        nextActiveRefs,
      );
    }

    return this.resolveChildSchemas(
      node,
      refMap,
      activeRefs,
    );
  }

  /**
   * Recursively resolves references contained inside a schema node.
   */
  private resolveChildSchemas(
    node: RawSchemaNode,
    refMap: RefMap,
    activeRefs: ReadonlySet<string>,
  ): RawSchemaNode {
    const resolved: RawSchemaNode = {
      ...node,
    };

    if (node.properties !== undefined) {
      resolved.properties = this.resolveSchemaRecord(
        node.properties,
        refMap,
        activeRefs,
      );
    }

    if (node.patternProperties !== undefined) {
      resolved.patternProperties =
        this.resolveSchemaRecord(
          node.patternProperties,
          refMap,
          activeRefs,
        );
    }

    if (node.dependentSchemas !== undefined) {
      resolved.dependentSchemas =
        this.resolveSchemaRecord(
          node.dependentSchemas,
          refMap,
          activeRefs,
        );
    }

    if (node.items !== undefined) {
      resolved.items = this.resolveRefs(
        node.items,
        refMap,
        new Set(activeRefs),
      );
    }

    if (node.prefixItems !== undefined) {
      resolved.prefixItems = node.prefixItems.map(
        (item) =>
          this.resolveRefs(
            item,
            refMap,
            new Set(activeRefs),
          ),
      );
    }

    if (node.contains !== undefined) {
      resolved.contains = this.resolveRefs(
        node.contains,
        refMap,
        new Set(activeRefs),
      );
    }

    if (node.propertyNames !== undefined) {
      resolved.propertyNames = this.resolveRefs(
        node.propertyNames,
        refMap,
        new Set(activeRefs),
      );
    }

    if (
      typeof node.additionalProperties === "object" &&
      node.additionalProperties !== null
    ) {
      resolved.additionalProperties =
        this.resolveRefs(
          node.additionalProperties,
          refMap,
          new Set(activeRefs),
        );
    }

    if (node.anyOf !== undefined) {
      resolved.anyOf = this.resolveSchemaArray(
        node.anyOf,
        refMap,
        activeRefs,
      );
    }

    if (node.oneOf !== undefined) {
      resolved.oneOf = this.resolveSchemaArray(
        node.oneOf,
        refMap,
        activeRefs,
      );
    }

    if (node.allOf !== undefined) {
      resolved.allOf = this.resolveSchemaArray(
        node.allOf,
        refMap,
        activeRefs,
      );
    }

    if (node.not !== undefined) {
      resolved.not = this.resolveRefs(
        node.not,
        refMap,
        new Set(activeRefs),
      );
    }

    if (node.if !== undefined) {
      resolved.if = this.resolveRefs(
        node.if,
        refMap,
        new Set(activeRefs),
      );
    }

    if (node.then !== undefined) {
      resolved.then = this.resolveRefs(
        node.then,
        refMap,
        new Set(activeRefs),
      );
    }

    if (node.else !== undefined) {
      resolved.else = this.resolveRefs(
        node.else,
        refMap,
        new Set(activeRefs),
      );
    }

    return resolved;
  }

  private resolveSchemaArray(
    schemas: RawSchemaNode[],
    refMap: RefMap,
    activeRefs: ReadonlySet<string>,
  ): RawSchemaNode[] {
    return schemas.map((schema) =>
      this.resolveRefs(
        schema,
        refMap,
        new Set(activeRefs),
      ),
    );
  }

  private resolveSchemaRecord(
    schemas: Record<string, RawSchemaNode>,
    refMap: RefMap,
    activeRefs: ReadonlySet<string>,
  ): Record<string, RawSchemaNode> {
    return Object.fromEntries(
      Object.entries(schemas).map(
        ([key, schema]) => [
          key,
          this.resolveRefs(
            schema,
            refMap,
            new Set(activeRefs),
          ),
        ],
      ),
    );
  }

  private parseProperty(
    key: string,
    rawProperty: RawSchemaNode,
    required = false,
  ): StepPropertySchema {
    const effectiveSchema =
      this.getEffectiveSchema(rawProperty);

    const editor = this.getEditor(
      key,
      rawProperty,
      effectiveSchema,
    );

    const structuredSchema = effectiveSchema;
    const childRequired = new Set(
      structuredSchema.required ?? [],
    );
    const alternatives = [
      ...(rawProperty.anyOf ?? []),
      ...(rawProperty.oneOf ?? []),
    ].filter((alternative) =>
      !this.isNullOnlySchema(alternative),
    );

    return {
      key,
      title:
        rawProperty.title ??
        effectiveSchema.title ??
        this.humanizeKey(key),
      description:
        rawProperty.description ??
        effectiveSchema.description ??
        "",
      help:
        rawProperty["crucible:help"] ??
        effectiveSchema["crucible:help"] ??
        null,
      editor,
      source: this.getSource(
        rawProperty,
        effectiveSchema,
        editor,
      ),
      enum: this.getEnum(
        rawProperty,
        effectiveSchema,
      ),
      hidden:
        rawProperty["crucible:hidden"] ??
        effectiveSchema["crucible:hidden"] ??
        false,
      advanced:
        rawProperty["crucible:advanced"] ??
        effectiveSchema["crucible:advanced"] ??
        false,
      type:
        rawProperty.type ??
        effectiveSchema.type ??
        (alternatives.length > 1 ? "union" : "string"),
      format:
        rawProperty.format ??
        effectiveSchema.format ??
        null,
      required,
      nullable: [
        ...(rawProperty.anyOf ?? []),
        ...(rawProperty.oneOf ?? []),
      ].some((alternative) =>
        this.isNullOnlySchema(alternative),
      ),
      hasDefault:
        this.hasOwn(rawProperty, "default") ||
        this.hasOwn(effectiveSchema, "default"),
      default: this.hasOwn(rawProperty, "default")
        ? rawProperty.default
        : effectiveSchema.default,
      constValue: this.hasOwn(rawProperty, "const")
        ? rawProperty.const
        : effectiveSchema.const,
      role:
        rawProperty["crucible:role"] ??
        effectiveSchema["crucible:role"] ??
        null,
      properties: Object.entries(
        structuredSchema.properties ?? {},
      ).map(([childKey, childSchema]) =>
        this.parseProperty(
          childKey,
          childSchema,
          childRequired.has(childKey),
        ),
      ),
      items: structuredSchema.items === undefined
        ? null
        : this.parseProperty(
          `${key}[]`,
          structuredSchema.items,
          true,
        ),
      alternatives: alternatives.map(
        (alternative, index) =>
          this.parseProperty(
            `${key}:${index}`,
            alternative,
            required,
          ),
      ),
      mapping: this.parseMapping(structuredSchema),
    };
  }

  private parseMapping(
    schema: RawSchemaNode,
  ): StepPropertySchema["mapping"] {
    if (
      schema.type !== "object" ||
      schema.additionalProperties === undefined ||
      schema.additionalProperties === false
    ) {
      return null;
    }

    const valueSchema =
      typeof schema.additionalProperties === "object"
        ? schema.additionalProperties
        : {};

    return {
      key: this.parseProperty(
        "$key",
        schema.propertyNames ?? { type: "string" },
        true,
      ),
      value: this.parseProperty(
        "$value",
        valueSchema,
        true,
      ),
    };
  }

  private hasOwn(
    value: object,
    key: string,
  ): boolean {
    return Object.prototype.hasOwnProperty.call(
      value,
      key,
    );
  }

  private humanizeKey(key: string): string {
    return key
      .replace(/\[\]$/, "")
      .replace(/^\$/, "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (character) =>
        character.toUpperCase(),
      );
  }

  /**
   * Gets the meaningful schema from nullable anyOf/oneOf declarations.
   *
   * Example:
   *
   * anyOf:
   *   - type: string
   *   - type: null
   *
   * returns the string schema.
   */
  private getEffectiveSchema(
    property: RawSchemaNode,
  ): RawSchemaNode {
    if (property.type !== undefined) {
      return property;
    }

    const alternatives = [
      ...(property.anyOf ?? []),
      ...(property.oneOf ?? []),
    ];

    const nonNullAlternative = alternatives.find(
      (option) =>
        option.type !== "null" &&
        !this.isNullOnlySchema(option),
    );

    return nonNullAlternative ?? property;
  }

  private isNullOnlySchema(
    schema: RawSchemaNode,
  ): boolean {
    return (
      schema.type === "null" ||
      schema.const === null
    );
  }

  private getEditor(
    key: string,
    property: RawSchemaNode,
    effectiveSchema: RawSchemaNode,
  ): StepPropertyEditorType {
    const propertyType =
      property.type ?? effectiveSchema.type;

    if (
      propertyType === "object" &&
      effectiveSchema.additionalProperties !== undefined
    ) {
      return "mapping-builder";
    }

    const configuredEditor =
      property["crucible:editor"] ??
      effectiveSchema["crucible:editor"];

    if (configuredEditor !== undefined) {
      return configuredEditor;
    }

    const crucibleType =
      property["crucible:type"] ??
      effectiveSchema["crucible:type"];

    if (crucibleType === "expression") {
      return "expression-builder";
    }

    if (key === "condition") {
      return "condition-builder";
    }

    if (propertyType === "array") {
      const itemType =
        effectiveSchema.items?.["crucible:type"];

      if (itemType === "column-name") {
        return "column-multiselect";
      }

      return "list-builder";
    }

    if (propertyType === "object") {
      return "object-editor";
    }

    const enumValues =
      property.enum ?? effectiveSchema.enum;

    if (enumValues !== undefined) {
      return "select";
    }

    const format =
      property.format ?? effectiveSchema.format;

    if (format === "date") {
      return "date-picker";
    }

    if (
      format === "date-time" ||
      format === "datetime"
    ) {
      return "datetime-picker";
    }

    switch (propertyType) {
      case "boolean":
        return "checkbox";

      case "integer":
      case "number":
        return "number";

      case undefined:
      case "union":
        return "value-editor";

      default:
        return "text";
    }
  }

  private getSource(
    property: RawSchemaNode,
    effectiveSchema: RawSchemaNode,
    editor: StepPropertyEditorType,
  ): StepPropertySource {
    const configuredSource =
      property["crucible:source"] ??
      effectiveSchema["crucible:source"];

    if (configuredSource !== undefined) {
      return configuredSource;
    }

    switch (editor) {
      case "column-select":
      case "column-multiselect":
        return "input-schema";

      case "file-picker":
      case "folder-picker":
        return "filesystem";

      case "select":
        return "enum";

      default:
        return "static";
    }
  }

  private getEnum(
    property: RawSchemaNode,
    effectiveSchema: RawSchemaNode,
  ): string[] | null {
    const rawValues =
      property.enum ?? effectiveSchema.enum;

    if (rawValues === undefined) {
      return null;
    }

    const values = rawValues.filter(
      (value): value is string =>
        typeof value === "string",
    );

    return values.length > 0
      ? values
      : null;
  }
}

export const stepSchemaParser =
  new StepSchemaParser();

import { Divider, Stack, Text } from "@mantine/core";

import type {
  StepPropertySchema,
  StepSchema,
} from "@/types/step_schema";

import { FieldEditor } from "./field_editor";
import type {
  StepEditorContext,
  StepFieldChange,
} from "./model";
import {
  DateEndpointEditor,
  JoinKeysEditor,
  ReplacementEditor,
} from "./special_editors";
import {
  applyStepFieldOverride,
  getStepSections,
  isStepFieldVisible,
} from "./step_specs";

type StepFormProps = {
  schema: StepSchema;
  context: StepEditorContext;
  onChange: StepFieldChange;
};

export function StepForm({
  schema,
  context,
  onChange,
}: StepFormProps) {
  const fields = schema.properties.map((field) =>
    applyStepFieldOverride(schema.key, field),
  );
  const fieldsByKey = Object.fromEntries(
    fields.map((field) => [field.key, field]),
  ) as Record<string, StepPropertySchema>;
  const sections = getStepSections(schema.key, fields);

  const updateTopLevel = (key: string, value: unknown) =>
    onChange([key], value);

  const renderField = (
    field: StepPropertySchema,
  ): React.ReactNode => {
    if (
      field.hidden ||
      !isStepFieldVisible(
        schema.key,
        field.key,
        context.parameters,
      )
    ) {
      return null;
    }

    if (schema.key === "join") {
      if (field.key === "right_on") {
        return null;
      }

      if (field.key === "left_on") {
        return (
          <JoinKeysEditor
            context={context}
            onChange={updateTopLevel}
          />
        );
      }
    }

    if (schema.key === "replace_values") {
      if (field.key === "new" || field.key === "mapping") {
        return null;
      }

      if (field.key === "old") {
        return (
          <ReplacementEditor
            fields={fieldsByKey}
            context={context}
            onChange={updateTopLevel}
          />
        );
      }
    }

    if (schema.key === "date_diff") {
      if (
        field.key === "start_value" ||
        field.key === "end_value"
      ) {
        return null;
      }

      if (field.key === "start_column") {
        return (
          <DateEndpointEditor
            label="Start"
            columnKey="start_column"
            valueKey="start_value"
            context={context}
            onChange={updateTopLevel}
          />
        );
      }

      if (field.key === "end_column") {
        return (
          <DateEndpointEditor
            label="End"
            columnKey="end_column"
            valueKey="end_value"
            context={context}
            onChange={updateTopLevel}
          />
        );
      }
    }

    return (
      <FieldEditor
        field={field}
        value={context.parameters[field.key]}
        context={context}
        onChange={(value) => onChange([field.key], value)}
      />
    );
  };

  return (
    <Stack gap="md">
      {sections.map((section) => {
        const sectionFields = section.fields
          .map((fieldKey) => fieldsByKey[fieldKey])
          .filter(
            (field): field is StepPropertySchema =>
              field !== undefined &&
              !field.hidden &&
              isStepFieldVisible(
                schema.key,
                field.key,
                context.parameters,
              ),
          );

        if (sectionFields.length === 0) {
          return null;
        }

        return (
          <Stack key={section.title} gap="sm">
            <div>
              <Text size="xs" fw={700} tt="uppercase" c="orange">
                {section.title}
              </Text>
              <Divider mt={4} />
            </div>

            {sectionFields.map((field) => (
              <div key={field.key}>
                {renderField(field)}
              </div>
            ))}
          </Stack>
        );
      })}
    </Stack>
  );
}

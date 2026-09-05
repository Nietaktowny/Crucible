import { useState } from "react";
import {
  Checkbox,
  Group,
  NumberInput,
  Select,
  Stack,
  Textarea,
  TextInput,
} from "@mantine/core";

type LiteralKind =
  | "string"
  | "number"
  | "boolean"
  | "null"
  | "json";

type LiteralValueEditorProps = {
  value: unknown;
  onChange: (value: unknown) => void;
  label?: string;
};

function getKind(value: unknown): LiteralKind {
  if (value === null) {
    return "null";
  }

  if (typeof value === "number") {
    return "number";
  }

  if (typeof value === "boolean") {
    return "boolean";
  }

  if (
    typeof value === "object" &&
    value !== undefined
  ) {
    return "json";
  }

  return "string";
}

function initialValueForKind(kind: LiteralKind): unknown {
  switch (kind) {
    case "number":
      return 0;
    case "boolean":
      return false;
    case "null":
      return null;
    case "json":
      return {};
    default:
      return "";
  }
}

function JsonTextEditor({
  value,
  onChange,
}: LiteralValueEditorProps) {
  const [text, setText] = useState(() =>
    JSON.stringify(value, null, 2),
  );
  const [error, setError] = useState<string | null>(null);

  return (
    <Textarea
      label="JSON value"
      value={text}
      error={error}
      autosize
      minRows={2}
      onChange={(event) => {
        const nextText = event.currentTarget.value;
        setText(nextText);

        try {
          onChange(JSON.parse(nextText));
          setError(null);
        } catch {
          setError("Enter valid JSON");
        }
      }}
    />
  );
}

export function LiteralValueEditor({
  value,
  onChange,
  label = "Value",
}: LiteralValueEditorProps) {
  const kind = getKind(value);

  return (
    <Stack gap="xs">
      <Select
        label={`${label} type`}
        value={kind}
        data={[
          { value: "string", label: "Text" },
          { value: "number", label: "Number" },
          { value: "boolean", label: "Boolean" },
          { value: "null", label: "Null" },
          { value: "json", label: "JSON" },
        ]}
        allowDeselect={false}
        onChange={(nextKind) => {
          if (nextKind !== null) {
            onChange(
              initialValueForKind(nextKind as LiteralKind),
            );
          }
        }}
      />

      {kind === "string" && (
        <TextInput
          label={label}
          value={typeof value === "string" ? value : ""}
          onChange={(event) =>
            onChange(event.currentTarget.value)
          }
        />
      )}

      {kind === "number" && (
        <NumberInput
          label={label}
          value={typeof value === "number" ? value : 0}
          onChange={(nextValue) =>
            onChange(
              typeof nextValue === "number"
                ? nextValue
                : 0,
            )
          }
        />
      )}

      {kind === "boolean" && (
        <Group>
          <Checkbox
            label={label}
            checked={value === true}
            onChange={(event) =>
              onChange(event.currentTarget.checked)
            }
          />
        </Group>
      )}

      {kind === "null" && (
        <TextInput
          label={label}
          value="null"
          disabled
        />
      )}

      {kind === "json" && (
        <JsonTextEditor
          key={JSON.stringify(value)}
          value={value}
          onChange={onChange}
        />
      )}
    </Stack>
  );
}

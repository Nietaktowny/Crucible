import { useContext, useState } from "react";
import { Modal, TextInput, Button, Group, Text, Stack } from "@mantine/core";
import { IconFlame } from "@tabler/icons-react";
import { notifications } from "@mantine/notifications";

import { ClientContext } from "@/context/api_context";
import { getErrorMessage } from "@/lib/format";

const NAME_PATTERN = /^[a-zA-Z0-9_.-]+$/;

type CreateWorkflowModalProps = {
  opened: boolean;
  onClose: () => void;
  onCreated: (name: string) => void;
};

export function CreateWorkflowModal({ opened, onClose, onCreated }: CreateWorkflowModalProps) {
  const client = useContext(ClientContext);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmedName = name.trim();
  const isValid = trimmedName.length > 0 && NAME_PATTERN.test(trimmedName);

  function reset() {
    setName("");
    setError(null);
    setCreating(false);
  }

  async function handleCreate() {
    if (!isValid || creating) {
      return;
    }

    setCreating(true);
    setError(null);

    try {
      await client.createWorkflow(trimmedName, { name: trimmedName, steps: [] });

      notifications.show({
        title: "Workflow created",
        message: `"${trimmedName}" is ready to build.`,
        color: "ember",
      });

      onCreated(trimmedName);
      reset();
      onClose();
    } catch (creationError) {
      setError(getErrorMessage(creationError));
    } finally {
      setCreating(false);
    }
  }

  return (
    <Modal
      opened={opened}
      onClose={() => {
        reset();
        onClose();
      }}
      title={
        <Group gap={8}>
          <IconFlame size={18} color="#f2600a" />
          <Text fw={700}>New workflow</Text>
        </Group>
      }
      centered
    >
      <Stack gap="md">
        <TextInput
          label="Workflow name"
          placeholder="sales_analysis"
          value={name}
          onChange={(event) => setName(event.currentTarget.value)}
          error={
            error ??
            (name.length > 0 && !isValid
              ? "Use only letters, numbers, dots, underscores and dashes."
              : null)
          }
          data-autofocus
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              void handleCreate();
            }
          }}
        />

        <Text size="xs" c="dimmed">
          Creates an empty workflow you can build out in the step editor.
        </Text>

        <Group justify="flex-end">
          <Button variant="subtle" color="gray" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="gradient"
            gradient={{ from: "#b23e08", to: "#ff9d3d", deg: 120 }}
            disabled={!isValid}
            loading={creating}
            onClick={() => void handleCreate()}
          >
            Create workflow
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

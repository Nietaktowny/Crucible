import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Group,
  Modal,
  Stack,
  Table,
  Text,
  Title,
  ActionIcon,
  Tooltip,
  TextInput,
  ThemeIcon,
  Skeleton,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  IconPlus,
  IconTrash,
  IconArrowRight,
  IconSearch,
  IconFlame,
  IconAlertTriangle,
} from "@tabler/icons-react";

import { ClientContext } from "@/context/api_context";
import type { WorkflowBasicDefinition } from "@/types/workflows";
import { CreateWorkflowModal } from "@/components/create_workflow_modal";
import { getErrorMessage } from "@/lib/format";

export function WorkflowsPage() {
  const client = useContext(ClientContext);
  const navigate = useNavigate();

  const [workflows, setWorkflows] = useState<WorkflowBasicDefinition[] | null>(null);
  const [search, setSearch] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<WorkflowBasicDefinition | null>(null);
  const [deleting, setDeleting] = useState(false);

  async function loadWorkflows() {
    try {
      const data = await client.getWorkflows();
      setWorkflows(data);
    } catch (error) {
      console.error("Failed to load workflows:", error);
      notifications.show({
        title: "Could not load workflows",
        message: getErrorMessage(error),
        color: "red",
      });
      setWorkflows([]);
    }
  }

  useEffect(() => {
    void loadWorkflows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleDelete() {
    if (pendingDelete === null) {
      return;
    }

    setDeleting(true);

    try {
      await client.deleteWorkflow(pendingDelete.name);
      notifications.show({
        title: "Workflow deleted",
        message: `"${pendingDelete.name}" was removed.`,
        color: "gray",
      });
      setPendingDelete(null);
      await loadWorkflows();
    } catch (error) {
      notifications.show({
        title: "Could not delete workflow",
        message: getErrorMessage(error),
        color: "red",
      });
    } finally {
      setDeleting(false);
    }
  }

  const filtered = (workflows ?? []).filter((workflow) =>
    workflow.name.toLowerCase().includes(search.trim().toLowerCase()),
  );

  return (
    <Stack gap="lg">
      <Group justify="space-between" align="flex-end">
        <Stack gap={2}>
          <Title order={2}>Workflows</Title>
          <Text c="dimmed" size="sm">
            Create, edit and run your data transformation pipelines.
          </Text>
        </Stack>

        <Button
          leftSection={<IconPlus size={16} />}
          variant="gradient"
          gradient={{ from: "#b23e08", to: "#ff9d3d", deg: 120 }}
          onClick={() => setCreateOpen(true)}
        >
          New workflow
        </Button>
      </Group>

      <TextInput
        placeholder="Search workflows…"
        leftSection={<IconSearch size={15} />}
        value={search}
        onChange={(event) => setSearch(event.currentTarget.value)}
        maw={320}
      />

      <Box className="fire-panel" style={{ overflow: "hidden" }}>
        {workflows === null ? (
          <Stack gap={0} p="md">
            <Skeleton height={44} radius="sm" mb={8} />
            <Skeleton height={44} radius="sm" mb={8} />
            <Skeleton height={44} radius="sm" />
          </Stack>
        ) : filtered.length === 0 ? (
          <Stack align="center" gap={6} py={60}>
            <ThemeIcon size={44} radius="xl" variant="light" color="ember">
              <IconFlame size={22} />
            </ThemeIcon>
            <Text fw={600}>No workflows found</Text>
            <Text size="sm" c="dimmed">
              {workflows.length === 0
                ? "Create your first workflow to start transforming data."
                : "Try a different search term."}
            </Text>
          </Stack>
        ) : (
          <Table highlightOnHover verticalSpacing="md" style={{ position: "relative", zIndex: 1 }}>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Name</Table.Th>
                <Table.Th>Path</Table.Th>
                <Table.Th w={120} ta="right">
                  Actions
                </Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {filtered.map((workflow) => (
                <Table.Tr
                  key={workflow.name}
                  style={{ cursor: "pointer" }}
                  onClick={() => navigate(`/workflows/${workflow.name}`)}
                >
                  <Table.Td>
                    <Group gap={10} wrap="nowrap">
                      <ThemeIcon variant="light" color="ember" size={28} radius="md">
                        <IconFlame size={15} />
                      </ThemeIcon>
                      <Text fw={600} size="sm">
                        {workflow.name}
                      </Text>
                    </Group>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed">
                      {workflow.path}
                    </Text>
                  </Table.Td>
                  <Table.Td onClick={(event) => event.stopPropagation()}>
                    <Group gap={4} justify="flex-end">
                      <Tooltip label="Open">
                        <ActionIcon
                          variant="subtle"
                          color="ember"
                          onClick={() => navigate(`/workflows/${workflow.name}`)}
                        >
                          <IconArrowRight size={16} />
                        </ActionIcon>
                      </Tooltip>
                      <Tooltip label="Delete">
                        <ActionIcon
                          variant="subtle"
                          color="red"
                          onClick={() => setPendingDelete(workflow)}
                        >
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Box>

      <CreateWorkflowModal
        opened={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(name) => navigate(`/workflows/${name}`)}
      />

      <Modal
        opened={pendingDelete !== null}
        onClose={() => setPendingDelete(null)}
        title={
          <Group gap={8}>
            <IconAlertTriangle size={18} color="#e03131" />
            <Text fw={700}>Delete workflow</Text>
          </Group>
        }
        centered
      >
        <Stack gap="md">
          <Text size="sm">
            Delete <strong>{pendingDelete?.name}</strong>? This removes the workflow file and
            cannot be undone.
          </Text>
          <Group justify="flex-end">
            <Button variant="subtle" color="gray" onClick={() => setPendingDelete(null)}>
              Cancel
            </Button>
            <Button color="red" loading={deleting} onClick={() => void handleDelete()}>
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}

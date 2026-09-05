import { useContext, useEffect, useMemo, useState } from "react";
import {
  ActionIcon,
  Box,
  Drawer,
  Group,
  Pagination,
  Skeleton,
  Stack,
  Table,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconAlertTriangle,
  IconChevronRight,
  IconHistory,
} from "@tabler/icons-react";

import type { WorkflowRunResult } from "@/types/workflows";
import { ClientContext } from "@/context/api_context";
import { StatusBadge } from "@/components/status_badge";
import { DynamicTable } from "@/components/dynamic_table";
import { formatDuration, formatNumber } from "@/lib/format";

type RunsTableProps = {
  workflow?: string;
  onRunsLoaded?: (runs: WorkflowRunResult[]) => void;
};

const PAGE_SIZE = 10;

export function RunsTable({ workflow, onRunsLoaded }: RunsTableProps) {
  const client = useContext(ClientContext);
  const [runs, setRuns] = useState<WorkflowRunResult[] | null>(null);
  const [page, setPage] = useState(1);
  const [selectedRun, setSelectedRun] = useState<WorkflowRunResult | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadRuns() {
      try {
        let data = await client.getAllRuns();

        if (workflow !== undefined) {
          data = data.filter((run) => run.name === workflow);
        }

        data.sort((a, b) => b.statistics.started_at.getTime() - a.statistics.started_at.getTime());

        if (!cancelled) {
          setRuns(data);
          onRunsLoaded?.(data);
        }
      } catch (error) {
        console.error("Failed to load runs:", error);
        if (!cancelled) {
          setRuns([]);
        }
      }
    }

    void loadRuns();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflow]);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil((runs?.length ?? 0) / PAGE_SIZE)),
    [runs],
  );

  const pageRuns = useMemo(() => {
    if (runs === null) {
      return [];
    }
    return runs.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  }, [runs, page]);

  if (runs === null) {
    return (
      <Stack gap={8}>
        <Skeleton height={40} radius="sm" />
        <Skeleton height={40} radius="sm" />
        <Skeleton height={40} radius="sm" />
      </Stack>
    );
  }

  if (runs.length === 0) {
    return (
      <Stack align="center" gap={6} py={60}>
        <ThemeIcon size={44} radius="xl" variant="light" color="ember">
          <IconHistory size={22} />
        </ThemeIcon>
        <Text fw={600}>No runs yet</Text>
        <Text size="sm" c="dimmed">
          Run a workflow to see its execution history here.
        </Text>
      </Stack>
    );
  }

  return (
    <Stack gap="md">
      <Box style={{ overflowX: "auto" }}>
        <Table highlightOnHover verticalSpacing="sm">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Workflow</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Started</Table.Th>
              <Table.Th>Duration</Table.Th>
              <Table.Th>Rows</Table.Th>
              <Table.Th w={40} />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {pageRuns.map((run) => (
              <Table.Tr
                key={run.run_id}
                style={{ cursor: "pointer" }}
                onClick={() => setSelectedRun(run)}
              >
                <Table.Td>
                  <Text size="sm" fw={600}>
                    {run.name}
                  </Text>
                  <Text size="xs" c="dimmed">
                    #{run.run_id.slice(0, 8)}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <StatusBadge status={run.status} />
                </Table.Td>
                <Table.Td>
                  <Text size="sm" c="dimmed">
                    {run.statistics.started_at.toLocaleString()}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{formatDuration(run.statistics.total_time)}</Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{formatNumber(run.row_count)}</Text>
                </Table.Td>
                <Table.Td>
                  <ActionIcon variant="subtle" color="gray">
                    <IconChevronRight size={16} />
                  </ActionIcon>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Box>

      {totalPages > 1 && (
        <Group justify="center">
          <Pagination total={totalPages} value={page} onChange={setPage} color="ember" />
        </Group>
      )}

      <Drawer
        opened={selectedRun !== null}
        onClose={() => setSelectedRun(null)}
        position="right"
        size="lg"
        title={
          <Group gap={8}>
            <Text fw={700}>Run detail</Text>
            {selectedRun && <StatusBadge status={selectedRun.status} />}
          </Group>
        }
      >
        {selectedRun && <RunDetail run={selectedRun} />}
      </Drawer>
    </Stack>
  );
}

function RunDetail({ run }: { run: WorkflowRunResult }) {
  return (
    <Stack gap="lg">
      <Stack gap={4}>
        <Title order={4}>{run.name}</Title>
        <Text size="xs" c="dimmed" ff="monospace">
          {run.run_id}
        </Text>
      </Stack>

      <Table withRowBorders={false} verticalSpacing={4}>
        <Table.Tbody>
          <DetailRow label="Started" value={run.statistics.started_at.toLocaleString()} />
          <DetailRow label="Finished" value={run.statistics.ended_at.toLocaleString()} />
          <DetailRow label="Duration" value={formatDuration(run.statistics.total_time)} />
          <DetailRow label="Rows produced" value={formatNumber(run.row_count)} />
          <DetailRow label="Total steps" value={formatNumber(run.statistics.total_steps)} />
          <DetailRow label="System steps" value={formatNumber(run.statistics.system_steps)} />
        </Table.Tbody>
      </Table>

      {run.error && (
        <Stack
          gap={6}
          p="md"
          style={{
            borderRadius: "var(--mantine-radius-md)",
            border: "1px solid rgba(224, 49, 49, 0.4)",
            background: "rgba(224, 49, 49, 0.08)",
          }}
        >
          <Group gap={6}>
            <IconAlertTriangle size={16} color="#e03131" />
            <Text fw={700} size="sm" c="red.4">
              Failed at step: {run.error.step_name || run.error.step_id}
            </Text>
          </Group>
          <Text
            component="pre"
            size="xs"
            c="red.2"
            style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0 }}
          >
            {run.error.error}
          </Text>
        </Stack>
      )}

      {run.preview && run.preview.length > 0 && (
        <Stack gap={6}>
          <Text fw={700} size="sm" tt="uppercase" c="ember.4" style={{ letterSpacing: "0.05em" }}>
            Output preview
          </Text>
          <DynamicTable data={run.preview.slice(0, 25)} />
        </Stack>
      )}
    </Stack>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <Table.Tr>
      <Table.Td c="dimmed" w={140}>
        {label}
      </Table.Td>
      <Table.Td fw={600}>{value}</Table.Td>
    </Table.Tr>
  );
}

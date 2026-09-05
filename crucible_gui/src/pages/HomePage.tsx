import { useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  Group,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  ThemeIcon,
  Title,
  Anchor,
} from "@mantine/core";
import {
  IconPlus,
  IconFolderOpen,
  IconCircleCheck,
  IconCircleX,
  IconClockHour4,
  IconArrowRight,
  IconFlame,
} from "@tabler/icons-react";

import { ClientContext } from "@/context/api_context";
import type { WorkflowBasicDefinition, WorkflowRunResult } from "@/types/workflows";
import { CrucibleMark } from "@/components/brand/CrucibleMark";
import { StatusBadge } from "@/components/status_badge";
import { CreateWorkflowModal } from "@/components/create_workflow_modal";
import { formatDuration, formatRelativeDate } from "@/lib/format";

export function HomePage() {
  const client = useContext(ClientContext);
  const navigate = useNavigate();

  const [workflows, setWorkflows] = useState<WorkflowBasicDefinition[] | null>(null);
  const [runs, setRuns] = useState<WorkflowRunResult[] | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [workflowsData, runsData] = await Promise.all([
          client.getWorkflows(),
          client.getAllRuns(),
        ]);

        if (!cancelled) {
          setWorkflows(workflowsData);
          setRuns(runsData);
        }
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
        if (!cancelled) {
          setWorkflows([]);
          setRuns([]);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [client]);

  const stats = useMemo(() => {
    if (runs === null) {
      return null;
    }

    const successCount = runs.filter((run) => run.status === "success").length;
    const failedCount = runs.filter((run) => run.status === "failed").length;
    const durations = runs
      .map((run) => run.statistics?.total_time)
      .filter((value): value is number => typeof value === "number");
    const avgDuration =
      durations.length > 0 ? durations.reduce((a, b) => a + b, 0) / durations.length : null;

    return { successCount, failedCount, avgDuration, total: runs.length };
  }, [runs]);

  const recentRuns = useMemo(() => {
    if (runs === null) {
      return [];
    }

    return [...runs]
      .sort((a, b) => b.statistics.started_at.getTime() - a.statistics.started_at.getTime())
      .slice(0, 6);
  }, [runs]);

  return (
    <Stack gap="xl">
      <Box
        className="fire-panel"
        p="xl"
        style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 24 }}
      >
        <Group gap="lg" wrap="nowrap" style={{ zIndex: 1, position: "relative" }}>
          <CrucibleMark size={64} />
          <Stack gap={4}>
            <Text size="xs" fw={700} tt="uppercase" c="ember.4" style={{ letterSpacing: "0.15em" }}>
              Welcome to
            </Text>
            <Title order={1} className="fire-text" style={{ fontSize: 40, lineHeight: 1 }}>
              CRUCIBLE
            </Title>
            <Text c="dimmed" size="sm" maw={420}>
              Transform your data. Build repeatable workflows. Get reliable results — all
              running locally on Polars.
            </Text>
          </Stack>
        </Group>

        <Group style={{ zIndex: 1, position: "relative" }}>
          <Button
            size="md"
            leftSection={<IconPlus size={18} />}
            variant="gradient"
            gradient={{ from: "#b23e08", to: "#ff9d3d", deg: 120 }}
            onClick={() => setCreateOpen(true)}
          >
            New workflow
          </Button>
          <Button
            size="md"
            variant="default"
            leftSection={<IconFolderOpen size={18} />}
            onClick={() => navigate("/workflows")}
          >
            Open workflow
          </Button>
        </Group>
      </Box>

      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <StatCard
          icon={IconCircleCheck}
          iconColor="teal"
          label="Successful runs"
          value={stats === null ? null : stats.successCount}
        />
        <StatCard
          icon={IconCircleX}
          iconColor="red"
          label="Failed runs"
          value={stats === null ? null : stats.failedCount}
        />
        <StatCard
          icon={IconClockHour4}
          iconColor="ember"
          label="Avg. run duration"
          value={stats === null ? null : formatDuration(stats.avgDuration)}
        />
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, lg: 2 }} spacing="lg">
        <Card withBorder radius="lg" p="lg" className="glow-card">
          <Group justify="space-between" mb="md">
            <Text fw={700} size="sm" tt="uppercase" c="ember.4" style={{ letterSpacing: "0.06em" }}>
              Recent workflows
            </Text>
            <Anchor size="xs" c="dimmed" onClick={() => navigate("/workflows")}>
              View all <IconArrowRight size={12} style={{ verticalAlign: "middle" }} />
            </Anchor>
          </Group>

          {workflows === null ? (
            <Stack gap="xs">
              <Skeleton height={36} radius="sm" />
              <Skeleton height={36} radius="sm" />
              <Skeleton height={36} radius="sm" />
            </Stack>
          ) : workflows.length === 0 ? (
            <EmptyRow label="No workflows yet. Create your first one to get started." />
          ) : (
            <Stack gap={2}>
              {workflows.slice(0, 6).map((workflow) => (
                <Group
                  key={workflow.name}
                  justify="space-between"
                  py={8}
                  px={10}
                  style={{ borderRadius: 8, cursor: "pointer" }}
                  onClick={() => navigate(`/workflows/${workflow.name}`)}
                  className="workflow-row"
                >
                  <Group gap={10} wrap="nowrap" style={{ minWidth: 0 }}>
                    <ThemeIcon variant="light" color="ember" size={28} radius="md">
                      <IconFlame size={15} />
                    </ThemeIcon>
                    <Box style={{ minWidth: 0 }}>
                      <Text size="sm" fw={600} truncate>
                        {workflow.name}
                      </Text>
                      <Text size="xs" c="dimmed" truncate>
                        {workflow.path}
                      </Text>
                    </Box>
                  </Group>
                </Group>
              ))}
            </Stack>
          )}
        </Card>

        <Card withBorder radius="lg" p="lg" className="glow-card">
          <Group justify="space-between" mb="md">
            <Text fw={700} size="sm" tt="uppercase" c="ember.4" style={{ letterSpacing: "0.06em" }}>
              Recent runs
            </Text>
            <Anchor size="xs" c="dimmed" onClick={() => navigate("/runs")}>
              View all <IconArrowRight size={12} style={{ verticalAlign: "middle" }} />
            </Anchor>
          </Group>

          {runs === null ? (
            <Stack gap="xs">
              <Skeleton height={36} radius="sm" />
              <Skeleton height={36} radius="sm" />
              <Skeleton height={36} radius="sm" />
            </Stack>
          ) : recentRuns.length === 0 ? (
            <EmptyRow label="No runs yet. Run a workflow to see history here." />
          ) : (
            <Stack gap={2}>
              {recentRuns.map((run) => (
                <Group key={run.run_id} justify="space-between" py={8} px={10}>
                  <Box style={{ minWidth: 0 }}>
                    <Text size="sm" fw={600} truncate>
                      {run.name}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {formatRelativeDate(run.statistics.started_at)} &middot;{" "}
                      {formatDuration(run.statistics.total_time)}
                    </Text>
                  </Box>
                  <StatusBadge status={run.status} />
                </Group>
              ))}
            </Stack>
          )}
        </Card>
      </SimpleGrid>

      <CreateWorkflowModal
        opened={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(name) => navigate(`/workflows/${name}`)}
      />
    </Stack>
  );
}

type StatCardProps = {
  icon: typeof IconCircleCheck;
  iconColor: string;
  label: string;
  value: string | number | null;
};

function StatCard({ icon: Icon, iconColor, label, value }: StatCardProps) {
  return (
    <Card withBorder radius="lg" p="lg" className="glow-card">
      <Group justify="space-between" align="flex-start">
        <Stack gap={2}>
          <Text size="xs" tt="uppercase" c="dimmed" fw={700} style={{ letterSpacing: "0.05em" }}>
            {label}
          </Text>
          {value === null ? (
            <Skeleton height={30} width={64} radius="sm" />
          ) : (
            <Text fw={700} size="28px" lh={1}>
              {value}
            </Text>
          )}
        </Stack>
        <ThemeIcon variant="light" color={iconColor} size={38} radius="md">
          <Icon size={20} />
        </ThemeIcon>
      </Group>
    </Card>
  );
}

function EmptyRow({ label }: { label: string }) {
  return (
    <Text size="sm" c="dimmed" py="md" ta="center">
      {label}
    </Text>
  );
}

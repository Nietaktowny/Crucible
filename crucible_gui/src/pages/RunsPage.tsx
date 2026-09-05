import { useMemo, useState } from "react";
import { Box, Card, Group, SimpleGrid, Stack, Text, ThemeIcon, Title } from "@mantine/core";
import { IconCircleCheck, IconCircleX, IconClockHour4, IconListDetails } from "@tabler/icons-react";

import { RunsTable } from "@/components/runs_table";
import type { WorkflowRunResult } from "@/types/workflows";
import { formatDuration } from "@/lib/format";

export function RunsPage() {
  const [runs, setRuns] = useState<WorkflowRunResult[]>([]);

  const stats = useMemo(() => {
    const successCount = runs.filter((run) => run.status === "success").length;
    const failedCount = runs.filter((run) => run.status === "failed").length;
    const durations = runs
      .map((run) => run.statistics?.total_time)
      .filter((value): value is number => typeof value === "number");
    const avgDuration =
      durations.length > 0 ? durations.reduce((a, b) => a + b, 0) / durations.length : null;

    return { successCount, failedCount, avgDuration, total: runs.length };
  }, [runs]);

  return (
    <Stack gap="lg">
      <Stack gap={2}>
        <Title order={2}>Recent runs</Title>
        <Text c="dimmed" size="sm">
          Review past executions, statuses and outputs.
        </Text>
      </Stack>

      <SimpleGrid cols={{ base: 2, sm: 4 }}>
        <MiniStat icon={IconListDetails} color="ember" label="Total runs" value={stats.total} />
        <MiniStat icon={IconCircleCheck} color="teal" label="Successful" value={stats.successCount} />
        <MiniStat icon={IconCircleX} color="red" label="Failed" value={stats.failedCount} />
        <MiniStat
          icon={IconClockHour4}
          color="ember"
          label="Avg. duration"
          value={formatDuration(stats.avgDuration)}
        />
      </SimpleGrid>

      <Box className="fire-panel" p="md">
        <RunsTable onRunsLoaded={setRuns} />
      </Box>
    </Stack>
  );
}

type MiniStatProps = {
  icon: typeof IconCircleCheck;
  color: string;
  label: string;
  value: string | number;
};

function MiniStat({ icon: Icon, color, label, value }: MiniStatProps) {
  return (
    <Card withBorder radius="lg" p="md" className="glow-card">
      <Group gap="sm" wrap="nowrap">
        <ThemeIcon variant="light" color={color} size={36} radius="md">
          <Icon size={18} />
        </ThemeIcon>
        <Stack gap={0}>
          <Text size="xs" c="dimmed" fw={600}>
            {label}
          </Text>
          <Text fw={700} size="lg" lh={1.2}>
            {value}
          </Text>
        </Stack>
      </Group>
    </Card>
  );
}

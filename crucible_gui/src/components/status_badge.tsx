import { Badge, type MantineColor } from "@mantine/core";
import {
  IconCheck,
  IconX,
  IconClock,
  IconPlayerPlay,
  IconMinus,
  IconBan,
} from "@tabler/icons-react";

import type { WorkflowStatus } from "@/types/workflows";

const STATUS_META: Record<
  WorkflowStatus,
  { label: string; color: MantineColor; icon: typeof IconCheck }
> = {
  success: { label: "Success", color: "teal", icon: IconCheck },
  failed: { label: "Failed", color: "red", icon: IconX },
  running: { label: "Running", color: "ember", icon: IconPlayerPlay },
  waiting: { label: "Waiting", color: "gray", icon: IconClock },
  created: { label: "Created", color: "gray", icon: IconMinus },
  cancelled: { label: "Cancelled", color: "yellow", icon: IconBan },
};

type StatusBadgeProps = {
  status: WorkflowStatus;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const meta = STATUS_META[status] ?? STATUS_META.created;
  const Icon = meta.icon;

  return (
    <Badge
      color={meta.color}
      variant={status === "success" || status === "failed" ? "light" : "outline"}
      radius="sm"
      leftSection={<Icon size={12} stroke={2.2} />}
      tt="none"
      fw={600}
    >
      {meta.label}
    </Badge>
  );
}

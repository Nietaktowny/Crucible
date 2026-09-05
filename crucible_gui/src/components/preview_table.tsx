import { useEffect, useState } from "react";
import { Group, Pagination, Stack, Text } from "@mantine/core";

import { DynamicTable } from "@/components/dynamic_table";

type PreviewRow = Record<string, unknown>;

type PreviewTableProps = {
  data: PreviewRow[];
};

const PAGE_SIZE = 200;

export function PreviewTable({ data }: PreviewTableProps) {
  const [pageIndex, setPageIndex] = useState(0);

  useEffect(() => {
    setPageIndex(0);
  }, [data]);

  if (data.length === 0) {
    return (
      <Text size="sm" c="dimmed" py="md" ta="center">
        No preview rows returned.
      </Text>
    );
  }

  const maxPages = Math.ceil(data.length / PAGE_SIZE);
  const safePageIndex = Math.min(pageIndex, maxPages - 1);

  const preview = data.slice(
    PAGE_SIZE * safePageIndex,
    PAGE_SIZE * safePageIndex + PAGE_SIZE
  );

  return (
    <Stack gap="sm">
      <DynamicTable data={preview} />

      {maxPages > 1 && (
        <Group justify="space-between">
          <Text size="xs" c="dimmed">
            {data.length.toLocaleString()} rows total
          </Text>
          <Pagination
            total={maxPages}
            value={safePageIndex + 1}
            onChange={(page) => setPageIndex(page - 1)}
            color="ember"
            size="sm"
          />
        </Group>
      )}
    </Stack>
  );
}

import { Group, Stack, Text } from "@mantine/core";

import { CrucibleMark } from "./CrucibleMark";

type CrucibleLogoProps = {
  size?: number;
  withTagline?: boolean;
};

export function CrucibleLogo({ size = 30, withTagline = true }: CrucibleLogoProps) {
  return (
    <Group gap="xs" wrap="nowrap">
      <CrucibleMark size={size} />
      <Stack gap={0}>
        <Text
          fw={700}
          size={size > 26 ? "lg" : "md"}
          lh={1.1}
          style={{
            fontFamily: "'Rajdhani', Inter, sans-serif",
            letterSpacing: "0.08em",
          }}
        >
          CRUCIBLE
        </Text>
        {withTagline && (
          <Text size="9px" c="dimmed" fw={600} lh={1} tt="uppercase" style={{ letterSpacing: "0.12em" }}>
            Data Workbench
          </Text>
        )}
      </Stack>
    </Group>
  );
}

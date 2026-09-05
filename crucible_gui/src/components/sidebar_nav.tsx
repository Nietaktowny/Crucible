import { Stack, Text, UnstyledButton, ThemeIcon, rem } from "@mantine/core";
import { Link, useLocation } from "react-router-dom";
import {
  IconHome2,
  IconSitemap,
  IconHistory,
  IconFlame,
} from "@tabler/icons-react";

const NAV_ITEMS = [
  { to: "/", label: "Home", icon: IconHome2, match: (path: string) => path === "/" },
  {
    to: "/workflows",
    label: "Workflows",
    icon: IconSitemap,
    match: (path: string) => path.startsWith("/workflows"),
  },
  { to: "/runs", label: "Runs", icon: IconHistory, match: (path: string) => path === "/runs" },
];

export function SidebarNavi() {
  const location = useLocation();

  return (
    <Stack gap={4} justify="space-between" h="100%">
      <Stack gap={4}>
        <Text
          size="10px"
          fw={700}
          c="dimmed"
          tt="uppercase"
          mb={4}
          style={{ letterSpacing: "0.1em" }}
        >
          Workspace
        </Text>

        {NAV_ITEMS.map((item) => {
          const active = item.match(location.pathname);
          const Icon = item.icon;

          return (
            <UnstyledButton
              key={item.to}
              component={Link}
              to={item.to}
              px="sm"
              py={8}
              style={{
                borderRadius: "var(--mantine-radius-md)",
                display: "flex",
                alignItems: "center",
                gap: rem(10),
                background: active
                  ? "linear-gradient(90deg, rgba(242,96,10,0.18), rgba(242,96,10,0.02))"
                  : "transparent",
                borderLeft: active
                  ? "2px solid #f2600a"
                  : "2px solid transparent",
                color: active ? "#ffd48a" : "#c8c9cd",
                transition: "background 120ms ease, color 120ms ease",
              }}
            >
              <ThemeIcon
                variant={active ? "gradient" : "light"}
                gradient={{ from: "#7c2d0f", to: "#f2600a", deg: 135 }}
                color="dark.5"
                size={28}
                radius="md"
              >
                <Icon size={16} stroke={1.8} />
              </ThemeIcon>
              <Text size="sm" fw={active ? 600 : 500}>
                {item.label}
              </Text>
            </UnstyledButton>
          );
        })}
      </Stack>

      <Stack
        gap={6}
        p="sm"
        style={{
          borderRadius: "var(--mantine-radius-md)",
          border: "1px solid var(--crucible-border)",
          background: "linear-gradient(160deg, #141517, #101113)",
        }}
      >
        <Text
          size="9px"
          fw={700}
          c="dimmed"
          tt="uppercase"
          style={{ letterSpacing: "0.1em", display: "flex", alignItems: "center", gap: 6 }}
        >
          <IconFlame size={12} color="#f2600a" />
          Engine
        </Text>
        <Text size="xs" c="dimmed">
          Polars (lazy) &middot; local
        </Text>
      </Stack>
    </Stack>
  );
}

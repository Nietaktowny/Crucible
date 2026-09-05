import { createTheme, type MantineColorsTuple } from "@mantine/core";

// "Ember" — the Crucible brand accent. Runs from pale glow to deep char.
const ember: MantineColorsTuple = [
  "#fff3e6",
  "#ffe0bf",
  "#ffc794",
  "#ffab68",
  "#ff8f42",
  "#ff7519",
  "#f2600a",
  "#d94e07",
  "#b23e08",
  "#7c2d0f",
];

// "Coal" — near-black neutrals used for the app chrome and surfaces.
const coal: MantineColorsTuple = [
  "#c8c9cd",
  "#aaacb1",
  "#8b8d93",
  "#6a6c72",
  "#4c4e54",
  "#34363b",
  "#232529",
  "#18191c",
  "#0f1011",
  "#08090a",
];

export const theme = createTheme({
  primaryColor: "ember",
  primaryShade: { light: 6, dark: 5 },
  colors: {
    ember,
    dark: coal,
  },
  fontFamily:
    "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif",
  fontFamilyMonospace:
    "'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, monospace",
  headings: {
    fontFamily:
      "'Rajdhani', Inter, 'Segoe UI', system-ui, sans-serif",
    fontWeight: "600",
  },
  defaultRadius: "md",
  black: "#08090a",
  white: "#f5f1ec",
  autoContrast: true,
  luminanceThreshold: 0.4,
  components: {
    Button: {
      defaultProps: {
        fw: 600,
      },
    },
    Paper: {
      defaultProps: {
        bg: "dark.7",
      },
    },
    Card: {
      defaultProps: {
        bg: "dark.7",
      },
    },
    Modal: {
      defaultProps: {
        overlayProps: { backgroundOpacity: 0.65, blur: 3 },
        radius: "lg",
      },
    },
    Table: {
      defaultProps: {
        verticalSpacing: "sm",
        horizontalSpacing: "md",
      },
    },
  },
});

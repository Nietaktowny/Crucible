import { BrowserRouter, Routes, Route, Outlet } from "react-router-dom";
import { AppShell, Box, Group } from "@mantine/core";

import { RunsPage } from "@/pages/RunsPage";
import { HomePage } from "@/pages/HomePage";
import { WorkflowsPage } from "@/pages/WorkflowsPage";
import { SidebarNavi } from "@/components/sidebar_nav";
import { WorkflowEditPage } from "@/pages/WorkflowEditPage";
import { CrucibleLogo } from "@/components/brand/CrucibleLogo";

function MainLayout() {
  return (
    <AppShell
      padding="lg"
      header={{ height: 60 }}
      navbar={{
        width: 250,
        breakpoint: "sm",
      }}
    >
      <AppShell.Header
        style={{
          background: "linear-gradient(180deg, #101113 0%, #0c0d0e 100%)",
          borderBottom: "1px solid var(--crucible-border)",
        }}
      >
        <Group h="100%" px="lg" justify="space-between">
          <CrucibleLogo size={28} />
        </Group>
      </AppShell.Header>

      <AppShell.Navbar
        p="md"
        style={{
          background: "#0c0d0e",
          borderRight: "1px solid var(--crucible-border)",
        }}
      >
        <SidebarNavi />
      </AppShell.Navbar>

      <AppShell.Main>
        <Box h="100%">
          <Outlet />
        </Box>
      </AppShell.Main>
    </AppShell>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/runs" element={<RunsPage />} />
          <Route path="/workflows" element={<WorkflowsPage />} />
          <Route path="/workflows/:workflowId" element={<WorkflowEditPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

import { useState } from "react";

import WorkflowEditorPage from "@/pages/WorkflowEditorPage";
import RunsHistoryPage from "@/pages/RunsHistoryPage";
import { Button } from "@/components/ui/button";

type Page = "editor" | "runs";

export default function App() {
  const [page, setPage] = useState<Page>("editor");
  const [darkMode, setDarkMode] = useState(true);

  return (
    <div className={darkMode ? "dark" : ""}>
      <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground">
        <header className="flex h-14 items-center gap-3 border-b px-4">
          <div className="font-semibold">Crucible</div>

          <Button
            variant={page === "editor" ? "default" : "outline"}
            onClick={() => setPage("editor")}
          >
            Workflow editor
          </Button>

          <Button
            variant={page === "runs" ? "default" : "outline"}
            onClick={() => setPage("runs")}
          >
            Runs history
          </Button>

          <Button
            className="ml-auto"
            variant="outline"
            onClick={() => setDarkMode((value) => !value)}
          >
            {darkMode ? "Light mode" : "Dark mode"}
          </Button>
        </header>

        <main className="min-h-0 flex-1 overflow-hidden">
          {page === "editor" && <WorkflowEditorPage />}
          {page === "runs" && <RunsHistoryPage />}
        </main>
      </div>
    </div>
  );
}
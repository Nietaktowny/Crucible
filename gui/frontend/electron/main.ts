import {
  app,
  BrowserWindow,
  dialog,
  ipcMain,
  globalShortcut,
  type IpcMainInvokeEvent,
  type OpenDialogOptions,
  type OpenDialogReturnValue,
} from "electron";
import { spawn, ChildProcess } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const isDev = !app.isPackaged;

const BACKEND_HOST = "127.0.0.1";
const BACKEND_PORT = "8000";
const BACKEND_BASE_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

let backend: ChildProcess | null = null;
let mainWindow: BrowserWindow | null = null;

async function showOpenDialogForEvent(
  event: IpcMainInvokeEvent,
  options: OpenDialogOptions,
): Promise<OpenDialogReturnValue> {
  const win = BrowserWindow.fromWebContents(event.sender);

  if (win) {
    return dialog.showOpenDialog(win, options);
  }

  return dialog.showOpenDialog(options);
}

function registerIpcHandlers() {
  ipcMain.handle("crucible:select-file-path", async (event) => {
    const result = await showOpenDialogForEvent(event, {
      title: "Select file",
      properties: ["openFile"],
      filters: [
        {
          name: "Supported files",
          extensions: ["csv", "xlsx", "xls", "json", "parquet", "yaml", "yml"],
        },
        {
          name: "All files",
          extensions: ["*"],
        },
      ],
    });

    return result.canceled || result.filePaths.length === 0
      ? null
      : result.filePaths[0];
  });

  ipcMain.handle("crucible:select-directory-path", async (event) => {
    const result = await showOpenDialogForEvent(event, {
      title: "Select folder",
      properties: ["openDirectory"],
    });

    return result.canceled || result.filePaths.length === 0
      ? null
      : result.filePaths[0];
  });
}

function getPackagedBackendPath() {
  return path.join(
    process.resourcesPath,
    "backend",
    "crucible-server.exe",
  );
}

function startBackend() {
  if (backend || isDev) {
    return;
  }

  backend = spawn(getPackagedBackendPath(), [], {
    shell: false,
    stdio: "ignore",
    windowsHide: true,
  });

  backend.on("error", (error) => {
    console.error("Failed to start backend:", error);
  });

  backend.on("exit", (code, signal) => {
    console.log(`Backend exited. code=${code}, signal=${signal}`);
    backend = null;
  });
}

function stopBackend() {
  if (!backend) {
    return;
  }

  backend.kill();
  backend = null;
}

async function waitForBackend(
  url: string,
  timeoutMs = 15000,
): Promise<void> {
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    try {
      const response = await fetch(url);

      if (response.ok) {
        return;
      }
    } catch {
      // Backend is not ready yet.
    }

    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  throw new Error(`Backend not available: ${url}`);
}

async function createWindow() {
  startBackend();

  try {
    await waitForBackend(`${BACKEND_BASE_URL}/docs`);
  } catch (error) {
    console.error(error);

    dialog.showErrorBox(
      "Crucible backend failed to start",
      String(error),
    );
  }

  const preloadPath = path.join(__dirname, "preload.cjs");

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    title: "Crucible",
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.webContents.openDevTools({
      mode: "detach",
    });

    await mainWindow.loadURL("http://localhost:5173");
  } else {
    await mainWindow.loadFile(
      path.join(__dirname, "../dist/index.html"),
    );
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  globalShortcut.register("Ctrl+Shift+I", () => {
    BrowserWindow.getFocusedWindow()?.webContents.toggleDevTools();
  });

  registerIpcHandlers();

  await createWindow();

  app.on("activate", async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createWindow();
    }
  });
});

app.on("before-quit", () => {
  stopBackend();
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
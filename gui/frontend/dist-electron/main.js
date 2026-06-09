import { app, BrowserWindow, dialog, ipcMain, globalShortcut, } from "electron";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const isDev = !app.isPackaged;
let backend = null;
function registerIpcHandlers() {
    ipcMain.handle("crucible:select-file-path", async (event) => {
        console.log("[IPC] crucible:select-file-path");
        const win = BrowserWindow.fromWebContents(event.sender);
        const result = await dialog.showOpenDialog(win, {
            title: "Select file",
            properties: ["openFile"],
            filters: [
                {
                    name: "Supported files",
                    extensions: [
                        "csv",
                        "xlsx",
                        "xls",
                        "json",
                        "parquet",
                        "yaml",
                        "yml",
                    ],
                },
                {
                    name: "All files",
                    extensions: ["*"],
                },
            ],
        });
        console.log("[IPC] file dialog result:", result);
        if (result.canceled || result.filePaths.length === 0) {
            return null;
        }
        return result.filePaths[0];
    });
    ipcMain.handle("crucible:select-directory-path", async (event) => {
        console.log("[IPC] crucible:select-directory-path");
        const win = BrowserWindow.fromWebContents(event.sender);
        const result = await dialog.showOpenDialog(win, {
            title: "Select folder",
            properties: ["openDirectory"],
        });
        console.log("[IPC] directory dialog result:", result);
        if (result.canceled || result.filePaths.length === 0) {
            return null;
        }
        return result.filePaths[0];
    });
}
function startBackend() {
    if (!isDev) {
        return;
    }
    backend = spawn("python", [
        "-m",
        "uvicorn",
        "crucible_server.app:create_app",
        "--factory",
        "--reload",
    ], {
        shell: true,
        stdio: "inherit",
    });
    backend.on("error", (error) => {
        console.error("Failed to start backend:", error);
    });
}
function stopBackend() {
    if (!backend) {
        return;
    }
    backend.kill();
    backend = null;
}
async function waitForBackend(url, timeoutMs = 15000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
        try {
            const response = await fetch(url);
            if (response.ok) {
                return;
            }
        }
        catch {
            // backend not ready yet
        }
        await new Promise((resolve) => setTimeout(resolve, 500));
    }
    throw new Error(`Backend not available: ${url}`);
}
async function createWindow() {
    if (isDev) {
        startBackend();
        await waitForBackend("http://127.0.0.1:8000/docs");
    }
    const preloadPath = path.join(__dirname, "preload.cjs");
    console.log("================================");
    console.log("Electron startup");
    console.log("isDev:", isDev);
    console.log("preload path:", preloadPath);
    console.log("================================");
    const win = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            preload: preloadPath,
            contextIsolation: true,
            nodeIntegration: false,
        },
    });
    win.webContents.openDevTools({
        mode: "detach",
    });
    if (isDev) {
        await win.loadURL("http://localhost:5173");
    }
    else {
        await win.loadFile(path.join(__dirname, "../dist/index.html"));
    }
}
app.whenReady().then(async () => {
    globalShortcut.register("Ctrl+Shift+I", () => {
        BrowserWindow.getFocusedWindow()?.webContents.toggleDevTools();
    });
    registerIpcHandlers();
    await createWindow();
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

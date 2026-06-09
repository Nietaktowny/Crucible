import { app, BrowserWindow } from "electron";
import path from "node:path";
const isDev = !app.isPackaged;
function createWindow() {
    const win = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });
    if (isDev) {
        win.loadURL("http://localhost:5173");
    }
    else {
        win.loadFile(path.join(__dirname, "../dist/index.html"));
    }
}
app.whenReady().then(createWindow);

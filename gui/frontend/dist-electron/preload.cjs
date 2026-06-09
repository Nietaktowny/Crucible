"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
console.log("Crucible preload loaded");
electron_1.contextBridge.exposeInMainWorld("crucible", {
    version: "1.0.0",
    selectFilePath: () => {
        return electron_1.ipcRenderer.invoke("crucible:select-file-path");
    },
    selectDirectoryPath: () => {
        return electron_1.ipcRenderer.invoke("crucible:select-directory-path");
    },
});

import { contextBridge, ipcRenderer } from "electron";

console.log("Crucible preload loaded");

contextBridge.exposeInMainWorld("crucible", {
  version: "1.0.0",

  selectFilePath: (): Promise<string | null> => {
    return ipcRenderer.invoke("crucible:select-file-path");
  },

  selectDirectoryPath: (): Promise<string | null> => {
    return ipcRenderer.invoke("crucible:select-directory-path");
  },
});
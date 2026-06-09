import { contextBridge } from "electron";

contextBridge.exposeInMainWorld("crucible", {
  version: "0.1.0",
});
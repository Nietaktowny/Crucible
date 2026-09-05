/// <reference types="vite/client" />

interface ImportMetaEnv {
  /**
   * Full override for the API base URL (e.g. "/api/v1" for a same-origin
   * reverse proxy in production, or "https://api.example.com/api/v1").
   * When unset, `CrucibleClient` builds a URL from its host/port arguments
   * instead (defaulting to `http://localhost:8000/api/v1` for local dev).
   */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

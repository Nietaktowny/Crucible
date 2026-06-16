export type WorkflowSummary = {
  name: string;
  path: string;
};

export type WorkflowListResponse = {
  workflows: WorkflowSummary[];
};

export type WorkflowResponse = {
  name: string;
  path: string;
  content: string;
};

export type PreviewRow = Record<string, unknown>;

export type WorkflowRunResponse = {
  workflow_name: string;
  success: boolean;
  message: string;
  preview: PreviewRow[] | null;
  row_count: number | null;
};

export type CachedPreview = {
  data: PreviewRow[];
  schema: Record<string, unknown>;
  row_count: number;
  preview_limit: number;
  stored_at: string;
};

const API_BASE_URL =
  import.meta.env.VITE_CRUCIBLE_API_URL ?? "http://127.0.0.1:8000/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const body = await response.json();
      message = body.message ?? body.detail ?? message;
    } catch {
      // Ignore non-JSON response.
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function requestNullable<T>(
  path: string,
  options: RequestInit = {},
): Promise<T | null> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const body = await response.json();
      message = body.message ?? body.detail ?? message;
    } catch {
      // Ignore non-JSON response.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export function listWorkflows(): Promise<WorkflowListResponse> {
  return request<WorkflowListResponse>("/workflows");
}

export function getWorkflow(name: string): Promise<WorkflowResponse> {
  return request<WorkflowResponse>(`/workflows/${encodeURIComponent(name)}`);
}

export function createWorkflow(
  name: string,
  content: string,
): Promise<WorkflowResponse> {
  return request<WorkflowResponse>("/workflows", {
    method: "POST",
    body: JSON.stringify({ name, content }),
  });
}

export function updateWorkflow(
  name: string,
  content: string,
): Promise<WorkflowResponse> {
  return request<WorkflowResponse>(`/workflows/${encodeURIComponent(name)}`, {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
}

export function deleteWorkflow(name: string): Promise<void> {
  return request<void>(`/workflows/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
}

export function runWorkflow(
  name: string,
  printPlan = false,
  inspect = true,
  previewLimit = 200,
): Promise<WorkflowRunResponse> {
  return request<WorkflowRunResponse>(
    `/runs/workflows/${encodeURIComponent(name)}`,
    {
      method: "POST",
      body: JSON.stringify({
        print_plan: printPlan,
        inspect,
        preview_limit: previewLimit,
      }),
    },
  );
}

export function getCachedPreview(
  name: string,
): Promise<CachedPreview | null> {
  return requestNullable<CachedPreview>(
    `/data/workflows/${encodeURIComponent(name)}/preview`,
  );
}

export type WorkflowStatus =
  | "created"
  | "success"
  | "failed"
  | "waiting"
  | "running"
  | "cancelled";

export type WorkflowRuntimeStatistics = {
  total_steps: number;
  system_steps: number;
  started_at: string | null;
  ended_at: string | null;
  total_time: number;
};

export type WorkflowErrorContext = {
  error: unknown;
  step_id: string;
  step_name: string;
  frame_schema: Record<string, string> | null;
};

export type WorkflowRunResult = {
  name: string;
  run_id: string;
  status: WorkflowStatus;
  preview?: PreviewRow[] | null;
  row_count: number | null;
  error: WorkflowErrorContext | null;
  statistics: WorkflowRuntimeStatistics;
  success: boolean;
};

export function listRuns(): Promise<WorkflowRunResult[]> {
  return request<WorkflowRunResult[]>("/data/runs");
}
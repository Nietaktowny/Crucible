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

export type WorkflowRunResponse = {
  workflow_name: string;
  success: boolean;
  message: string;
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
): Promise<WorkflowRunResponse> {
  return request<WorkflowRunResponse>(
    `/runs/workflows/${encodeURIComponent(name)}`,
    {
      method: "POST",
      body: JSON.stringify({ print_plan: printPlan }),
    },
  );
}
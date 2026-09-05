export type WorkflowBasicDefinition = {
  name: string;
  path: string;
};

export interface StepConfig {
  step_id: string;
  name: string;
  key: string;
  description: string;
  parameters: Record<string, unknown>;
}

export interface WorkflowConfig {
  name: string;
  steps: StepConfig[];  
}

export interface WorkflowFullConfig {
  name: string;
  path: string;
  content: WorkflowConfig;
}

export interface WorkflowRunRequest {
  print_plan: boolean;
  preview_limit: number;
  inspect: boolean;
}

export interface WorkflowRunResponse {
  workflow_name: string;
  success: boolean;
  message: string;
  preview: any[];
  row_count: number | null
}

export interface CachedPreview {
  data: any[];
  frame_schema: Record<string, unknown>;
  row_count: number;
  preview_limit: number;
  stored_at: string;
}

export type WorkflowStatus = 
| "created"
| "success"
| "failed"
| "waiting"
| "running"
| "cancelled";

export interface WorkflowRunStatistics {
  ended_at: Date;
  started_at: Date;
  system_steps: number;
  total_steps: number;
  total_time: number;
}

export interface WorkflowErrorContext {
  error: string;
  step_id: string;
  step_name: string;
  frame_schema: Record<string, string> | null;
}

export interface WorkflowRunResult {
    run_id: string;
    name: string;
    status: WorkflowStatus;
    statistics: WorkflowRunStatistics;
    preview: any[] | null;
    row_count: number | null;
    error: WorkflowErrorContext | null;
}

/**
 * Shape of the JSON body returned by the server for a failed run, whether
 * a known `workflow_run_failed` (a step raised during execution) or an
 * `internal_server_error` (anything unexpected). `step_name`/`step_id`/
 * `frame_schema` are only present for the former.
 */
export interface WorkflowRunErrorBody {
  error: "workflow_run_failed" | "internal_server_error" | string;
  message: string;
  workflow_name?: string;
  step_id?: string;
  step_name?: string;
  frame_schema?: Record<string, string> | null;
  traceback?: string;
}
import type { 
  WorkflowBasicDefinition,
  WorkflowFullConfig,
  WorkflowRunRequest,
  WorkflowConfig,
  WorkflowRunResponse,
  CachedPreview,
  WorkflowRunResult,
} from "@/types/workflows";

import type {
  StepSchema,
} from "@/types/step_schema";

import {
  stepSchemaParser,
  type RawStepSchema,
} from "@/parsers/step_schema_parser";

import YAML from "yaml";

export class CrucibleClient {
  #host: string;
  #port: number;
  #apiVersion: string;
  #baseUrl: string;

  constructor(
    host: string = "localhost",
    port: number = 8000,
    apiVersion: string = "v1",
  ) {
    this.#host = host;
    this.#port = port;
    this.#apiVersion = apiVersion;

    this.#baseUrl = this.#buildBaseUrl();
  }

  #buildBaseUrl(): string {
    // In production the frontend is typically built with VITE_API_BASE_URL
    // set to a same-origin path (e.g. "/api/v1") so a reverse proxy can
    // forward it to the backend without needing CORS or a hardcoded host.
    const override = import.meta.env.VITE_API_BASE_URL;

    if (override) {
      return override.replace(/\/+$/, "");
    }

    return `http://${this.#host}:${this.#port}/api/${this.#apiVersion}`;
  }

  configure(
    host: string,
    port: number,
    apiVersion: string,
  ): void {
    this.#host = host;
    this.#port = port;
    this.#apiVersion = apiVersion;

    this.#baseUrl = this.#buildBaseUrl();
  }

  async get(urlPath: string): Promise<any> {
    const url = `${this.#baseUrl}/${urlPath}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch data from server. URL: ${urlPath}`)
    }

    if (!response.ok) {
      console.error(response)
      throw new Error(`Error during GET to path '${urlPath}'`, {
        "cause": await response.json()
      })
    }

    return (await response.json())
  }

  async post(urlPath: string, body: any): Promise<any> {
    const url = `${this.#baseUrl}/${urlPath}`;

    const response = await fetch(
      url,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      }
    );

    if (!response.ok) {
      console.error(response)
      throw new Error(`Error during POST to path '${urlPath}'`, {
        "cause": await response.json()
      })
    }

    return await response.json();
  }

  async put(urlPath: string, body: any): Promise<any> {
    const url = `${this.#baseUrl}/${urlPath}`;

    const response = await fetch(
      url,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      }
    );

    if (!response.ok) {
      console.error(response)
      throw new Error(`Error during PUT to path '${urlPath}'`, {
        "cause": await response.json()
      })
    }

    return await response.json();
  }

  async delete(urlPath: string): Promise<any> {
    const url = `${this.#baseUrl}/${urlPath}`;

    const response = await fetch(
      url,
      {
        method: 'DELETE'
      }
    );

    if (!response.ok) {
      console.error(response)
      throw new Error(`Error during DELETE to path '${urlPath}'`, {
        "cause": await response.json()
      })
    }

    return response.status === 204;
  }

  async getWorkflows(): Promise<WorkflowBasicDefinition[]> {
    let data = await this.get("workflows");
    data = data['workflows'] as WorkflowBasicDefinition[];
    console.debug(`Got workflows basic definitions: ${data}`)
    return data;
  }

  async getWorkflow(name: string): Promise<WorkflowFullConfig> {
    const data = await this.get("workflows/" + name);
    return data as WorkflowFullConfig;
  }

  async createWorkflow(workflowName: string, content: WorkflowConfig): Promise<WorkflowFullConfig> {
    const data = {
      "name": workflowName,
      "content": YAML.stringify(content)
    }
    let result = await this.post("workflows", data);
    return result as WorkflowFullConfig;
  }

  async updateWorkflow(workflowName: string, content: WorkflowConfig): Promise<WorkflowFullConfig> {
    const data = {
      "content": YAML.stringify(content)
    }
    let result = await this.put("workflows/" + workflowName, data);
    return result as WorkflowFullConfig;
  }

  async deleteWorkflow(workflowName: string): Promise<boolean> {
    return await this.delete("workflows/" + workflowName)
  }

  async getStepsSchema(): Promise<StepSchema[]> {
    const data = await this.get("data/steps_schema") as RawStepSchema[];
    return stepSchemaParser.parse(data);
  }

  async runWorkflow(workflowName: string): Promise<any> {
    const body: WorkflowRunRequest = {
      "inspect": true,
      "preview_limit": 200,
      "print_plan": true
    };

    const data = await this.post("runs/workflows/" + workflowName, body);
    return data as WorkflowRunResponse;
  }

  async getCachedPreview(workflowName: string): Promise<CachedPreview> {
    const data = await this.get("data/workflows/" + workflowName + "/preview");
    return data as CachedPreview;
  }

  async getExcelSheets(path: string): Promise<string[]> {
    const body = {
      "path": path
    }
    const data = await this.post("data/files/sheets", body);
    return data as string[];
  }

  async getAllRuns(): Promise<WorkflowRunResult[]> {
    const data = await this.get("data/runs") as WorkflowRunResult[];
    data.forEach((item) => {
      item.statistics.ended_at = new Date(item.statistics.ended_at)
      item.statistics.started_at = new Date(item.statistics.started_at)
    })
    return data;
  }

}

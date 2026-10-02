import type {
  ClassifyResponse,
  CustomerOut,
  HealthOut,
  SampleInteraction,
  TaskListItem,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export { ApiError };

export function getHealth(): Promise<HealthOut> {
  return request<HealthOut>("/api/health");
}

export function getCustomers(): Promise<CustomerOut[]> {
  return request<CustomerOut[]>("/api/customers");
}

export function getSampleInteractions(): Promise<SampleInteraction[]> {
  return request<SampleInteraction[]>("/api/interactions");
}

export function getTasks(): Promise<TaskListItem[]> {
  return request<TaskListItem[]>("/api/tasks");
}

export function classifyByInteractionId(interactionId: string): Promise<ClassifyResponse> {
  return request<ClassifyResponse>("/api/classify", {
    method: "POST",
    body: JSON.stringify({ interactionId }),
  });
}

export function classifyFreeText(args: {
  customerId: string;
  channel: "phone_note" | "web_form" | "whatsapp_mock";
  text: string;
}): Promise<ClassifyResponse> {
  return request<ClassifyResponse>("/api/classify", {
    method: "POST",
    body: JSON.stringify(args),
  });
}

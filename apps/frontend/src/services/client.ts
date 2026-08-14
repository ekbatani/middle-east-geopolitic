import { ProblemDetails } from "../types";

export class ApiError extends Error {
  public status: number;
  public problem?: ProblemDetails;
  public details?: unknown;

  constructor(message: string, status: number, problem?: ProblemDetails, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
    this.details = details;
  }
}

export function getNormalizedApiUrl(rawUrl?: string): string {
  let url = (rawUrl || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim();
  if (!url) return "http://localhost:8000";
  if (!/^https?:\/\//i.test(url) && !url.startsWith("/")) {
    url = `http://${url}`;
  }
  return url.replace(/\/+$/, "");
}

export const AUTH_STORAGE_KEYS = {
  TOKEN: "mei_jwt_token",
  API_KEY: "mei_api_key",
};

export function getStoredAuth(): { token: string | null; apiKey: string | null } {
  if (typeof window === "undefined") {
    return { token: null, apiKey: null };
  }
  return {
    token: localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN),
    apiKey: localStorage.getItem(AUTH_STORAGE_KEYS.API_KEY),
  };
}

export function setStoredAuth(token?: string | null, apiKey?: string | null): void {
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem(AUTH_STORAGE_KEYS.TOKEN, token);
  } else if (token === null) {
    localStorage.removeItem(AUTH_STORAGE_KEYS.TOKEN);
  }

  if (apiKey) {
    localStorage.setItem(AUTH_STORAGE_KEYS.API_KEY, apiKey);
  } else if (apiKey === null) {
    localStorage.removeItem(AUTH_STORAGE_KEYS.API_KEY);
  }
}

export type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  params?: Record<string, string | number | boolean | null | undefined>;
  body?: unknown;
  headers?: Record<string, string>;
  token?: string | null;
  apiKey?: string | null;
};

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const baseUrl = getNormalizedApiUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${baseUrl}${normalizedPath}`);

  if (options.params) {
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.append(key, String(value));
      }
    });
  }

  const headers: Record<string, string> = {
    "Accept": "application/json",
    ...options.headers,
  };

  if (options.body !== undefined && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  // Inject authentication header
  const stored = getStoredAuth();
  const activeToken = options.token ?? stored.token;
  const activeApiKey = options.apiKey ?? stored.apiKey;

  if (activeToken) {
    headers["Authorization"] = `Bearer ${activeToken}`;
  } else if (activeApiKey) {
    headers["Authorization"] = `Bearer ${activeApiKey}`;
  }

  const fetchOptions: RequestInit = {
    method: options.method || "GET",
    headers,
  };

  if (options.body !== undefined) {
    fetchOptions.body = options.body instanceof FormData ? options.body : JSON.stringify(options.body);
  }

  let response: Response;
  try {
    response = await fetch(url.toString(), fetchOptions);
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "Network error connecting to API",
      0
    );
  }

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    let problem: ProblemDetails | undefined;
    let jsonBody: unknown;

    try {
      jsonBody = await response.json();
      if (jsonBody && typeof jsonBody === "object") {
        const obj = jsonBody as Record<string, unknown>;
        if (typeof obj.detail === "string") {
          errorDetail = obj.detail;
        } else if (typeof obj.title === "string") {
          errorDetail = obj.title;
        }
        if (typeof obj.title === "string" && typeof obj.status === "number") {
          problem = jsonBody as ProblemDetails;
        }
      }
    } catch {
      // response wasn't JSON
    }

    throw new ApiError(errorDetail, response.status, problem, jsonBody);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  return (await response.text()) as unknown as T;
}

export const apiClient = {
  get: <T>(path: string, params?: RequestOptions["params"], options?: Omit<RequestOptions, "method" | "params">) =>
    request<T>(path, { ...options, method: "GET", params }),

  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "POST", body }),

  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "PATCH", body }),

  delete: <T>(path: string, options?: Omit<RequestOptions, "method">) =>
    request<T>(path, { ...options, method: "DELETE" }),
};

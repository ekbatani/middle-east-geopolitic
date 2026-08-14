export type UUID = string;

export type ScopeType = "country" | "regional" | "global" | "actor" | "topic";

export type Trend = "rising" | "falling" | "stable";

export type VerificationStatus = "unverified" | "corroborated" | "confirmed" | "debunked" | "disputed";

export type LifecycleStatus = "candidate" | "active" | "archived" | "rejected";

export type ProblemDetails = {
  type?: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
};

export type PaginationParams = {
  limit?: number;
  offset?: number;
};

export type HealthStatus = {
  status: string;
  details?: Record<string, unknown>;
};

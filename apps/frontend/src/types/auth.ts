import { UUID } from "./common";

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
  scopes: string[];
};

export type CurrentPrincipal = {
  user_id: UUID;
  scopes: string[];
  api_key_id?: UUID;
};

export const SCOPES = {
  INTELLIGENCE_READ: "intelligence:read",
  SOURCES_SUBMIT: "sources:submit",
  INVESTIGATIONS_CREATE: "investigations:create",
  INVESTIGATIONS_READ: "investigations:read",
  EVENTS_CREATE: "events:create",
  EVENTS_APPROVE: "events:approve",
  CLAIMS_CREATE: "claims:create",
  CLAIMS_ASSESS: "claims:assess",
  RELATIONSHIPS_ASSESS: "relationships:assess",
  RISKS_RECALCULATE: "risks:recalculate",
  SCENARIOS_SIMULATE: "scenarios:simulate",
  REPORTS_GENERATE: "reports:generate",
  REPORTS_APPROVE: "reports:approve",
  MONITORS_MANAGE: "monitors:manage",
  IMAGERY_SUBMIT: "imagery:submit",
  REVIEW_RESOLVE: "review:resolve",
  ANALYST_ASSESSMENTS_RECORD: "analyst_assessments:record",
  ADMIN_CONFIGURATION: "admin:configuration",
} as const;

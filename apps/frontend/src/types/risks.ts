import { ScopeType, Trend, UUID } from "./common";

export type RiskApprovalStatus = "draft" | "under_review" | "approved" | "rejected";

export type RiskDefinition = {
  id: UUID;
  code: string;
  name: string;
  description?: string | null;
  scope_types: string[];
  ruleset_version: string;
};

export type RiskAssessment = {
  id: UUID;
  risk_definition_id: UUID;
  scope_type: ScopeType;
  scope_id?: UUID | null;
  assessed_at: string;
  base_score: number;
  llm_adjustment: number;
  final_score: number;
  previous_score?: number | null;
  trend?: Trend | null;
  confidence: number;
  explanation?: string | null;
  counter_indicators: string[];
  evidence_bundle_id?: UUID | null;
  ruleset_version: string;
  model_version?: string | null;
  approval_status: RiskApprovalStatus;
  approved_by?: string | null;
  approved_at?: string | null;
};

export type RiskCatalogItem = {
  definition: RiskDefinition;
  latest_assessment?: RiskAssessment | null;
};

export type RecalculateRiskRequest = {
  risk_definition_id: UUID;
  scope_type: ScopeType;
  scope_id?: UUID | null;
};

export type Contribution = {
  indicator_code: string;
  indicator_name: string;
  weight: number;
  direction: string;
  raw_value?: number | null;
  normalized_value?: number | null;
  contribution?: number | null;
  confidence?: number | null;
  observed_at?: string | null;
  included: boolean;
  stale: boolean;
};

export type RiskExplanation = {
  risk_definition_id: UUID;
  risk_code: string;
  risk_name: string;
  scope_type: ScopeType;
  scope_id?: UUID | null;
  assessed_at: string;
  base_score: number;
  llm_adjustment: number;
  final_score: number;
  previous_score?: number | null;
  trend: string;
  confidence: number;
  explanation: string;
  changed_indicators: string[];
  counter_indicators: string[];
  contributions: Contribution[];
  evidence_ids: UUID[];
  ruleset_version: string;
  model_version?: string | null;
};

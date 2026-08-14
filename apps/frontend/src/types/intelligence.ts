import { UUID } from "./common";

export type RiskDimension = {
  score: number;
  previous_score?: number | null;
  trend: string;
  confidence: number;
  explanation: string;
  changed_indicators: string[];
  counter_indicators: string[];
  evidence_ids: UUID[];
};

export type RelationshipComparisonRequest = {
  relationship_ids: UUID[];
  as_of: string;
  include_evidence?: boolean;
};

export type RelationshipComparisonItem = {
  relationship_id: UUID;
  source_actor: string;
  target_actor: string;
  diplomatic: RiskDimension;
  military_tension: RiskDimension;
  economic_dependency: RiskDimension;
  strategic_trust: RiskDimension;
  proxy_competition: RiskDimension;
  escalation_risk: RiskDimension;
};

export type CountryBriefRequest = {
  country_actor_id: UUID;
  as_of?: string | null;
};

export type CountryBriefRiskOut = {
  risk_code: string;
  risk_name: string;
  dimension: RiskDimension;
};

export type CountryBriefRelationshipOut = {
  relationship_id: UUID;
  counterpart_actor_id: UUID;
  counterpart_name: string;
  relationship_type: string;
  escalation_risk_score?: number | null;
  trend?: string | null;
  confidence?: number | null;
};

export type CountryBriefResponse = {
  country_actor_id: UUID;
  country_name: string;
  as_of: string;
  risks: CountryBriefRiskOut[];
  relationships: CountryBriefRelationshipOut[];
};

export type SearchItem = {
  id: UUID;
  type: "actor" | "event" | "claim" | "document";
  title: string;
  detail?: string | null;
};

export type IntelligenceSearchRequest = {
  query: string;
  limit?: number;
};

export type EventInvestigationRequest = {
  event_id: UUID;
  priority?: string;
};

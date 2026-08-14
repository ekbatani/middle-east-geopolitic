import { ScopeType, UUID } from "./common";

export type ScenarioFamily =
  | "status_quo"
  | "rapid_escalation"
  | "de_escalation"
  | "regime_crisis"
  | "proxy_shift"
  | "economic_collapse";

export type ScenarioStatus = "active" | "dormant" | "realized" | "invalidated";

export type Scenario = {
  id: UUID;
  name: string;
  scope_type: ScopeType;
  scope_id?: UUID | null;
  scenario_family: ScenarioFamily;
  time_horizon: string;
  status: ScenarioStatus;
  description?: string | null;
};

export type ScenarioAssessment = {
  id: UUID;
  scenario_id: UUID;
  assessed_at: string;
  probability_low: number;
  probability_high: number;
  confidence: number;
  assumptions: string[];
  trigger_events: string[];
  leading_indicators: string[];
  expected_actor_behavior?: string | null;
  military_consequences?: string | null;
  economic_consequences?: string | null;
  humanitarian_consequences?: string | null;
  invalidation_criteria: string[];
  explanation_of_change?: string | null;
  evidence_bundle_id?: UUID | null;
  model_version?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
};

export type CreateScenarioRequest = {
  name: string;
  scope_type: ScopeType;
  scope_id?: UUID | null;
  scenario_family: ScenarioFamily;
  time_horizon: string;
  description?: string | null;
};

export type ScenarioSimulationRequest = {
  scope_type: ScopeType;
  scope_id?: UUID | null;
  scenario_family: ScenarioFamily;
  time_horizon: string;
  hypothetical_context: string;
};

export type ScenarioUpdateRecommendation = {
  probability_low: number;
  probability_high: number;
  confidence: number;
  assumptions: string[];
  trigger_events: string[];
  leading_indicators: string[];
  expected_actor_behavior?: string | null;
  military_consequences?: string | null;
  economic_consequences?: string | null;
  humanitarian_consequences?: string | null;
  invalidation_criteria: string[];
  explanation_of_change?: string | null;
};

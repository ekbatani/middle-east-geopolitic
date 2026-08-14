import { Trend, UUID } from "./common";

export type RelationshipDirectionality = "directed" | "symmetric";

export type RelationshipStatus = "active" | "dormant" | "historic" | "terminated";

export type Relationship = {
  id: UUID;
  source_actor_id: UUID;
  target_actor_id: UUID;
  relationship_type: string;
  directionality: RelationshipDirectionality;
  status: RelationshipStatus;
};

export type RelationshipObservation = {
  id: UUID;
  relationship_id: UUID;
  observed_at: string;
  diplomatic_score?: number | null;
  military_cooperation_score?: number | null;
  military_tension_score?: number | null;
  intelligence_cooperation_score?: number | null;
  economic_dependency_score?: number | null;
  energy_dependency_score?: number | null;
  strategic_trust_score?: number | null;
  ideological_compatibility_score?: number | null;
  proxy_competition_score?: number | null;
  public_hostility_score?: number | null;
  escalation_risk_score?: number | null;
  trend?: Trend | null;
  confidence?: number | null;
  explanation?: string | null;
  evidence_bundle_id?: UUID | null;
  ruleset_version?: string | null;
  model_version?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
};

export type CreateRelationshipRequest = {
  source_actor_id: UUID;
  target_actor_id: UUID;
  relationship_type: string;
  directionality?: RelationshipDirectionality;
};

export type AssessRelationshipRequest = {
  diplomatic_score?: number | null;
  military_cooperation_score?: number | null;
  military_tension_score?: number | null;
  intelligence_cooperation_score?: number | null;
  economic_dependency_score?: number | null;
  energy_dependency_score?: number | null;
  strategic_trust_score?: number | null;
  ideological_compatibility_score?: number | null;
  proxy_competition_score?: number | null;
  public_hostility_score?: number | null;
  escalation_risk_score?: number | null;
  trend?: Trend | null;
  confidence?: number | null;
  explanation?: string | null;
  evidence_bundle_id?: UUID | null;
  ruleset_version?: string;
};

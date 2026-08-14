import { UUID } from "./common";

export type DisagreementSubjectType = "claim" | "event" | "risk_assessment" | "scenario" | "relationship";

export type AnalystAssessment = {
  id: UUID;
  subject_type: DisagreementSubjectType;
  subject_id: UUID;
  analyst_user_id?: UUID | null;
  stance?: string | null;
  score?: number | null;
  confidence?: number | null;
  rationale?: string | null;
  evidence_bundle_id?: UUID | null;
  created_at: string;
  updated_at: string;
};

export type RecordPositionRequest = {
  subject_type: DisagreementSubjectType;
  subject_id: UUID;
  stance?: string | null;
  score?: number | null;
  confidence?: number | null;
  rationale?: string | null;
  evidence_bundle_id?: UUID | null;
};

export type DisagreementSummary = {
  subject_type: DisagreementSubjectType;
  subject_id: UUID;
  position_count: number;
  distinct_stances: number;
  score_spread?: number | null;
};

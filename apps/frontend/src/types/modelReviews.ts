import { UUID } from "./common";

export type ModelReviewSubjectType = "risk_assessment" | "scenario_assessment" | "event_assessment";

export type ModelReviewResult = {
  id: UUID;
  subject_type: ModelReviewSubjectType;
  subject_id: UUID;
  trigger_reason: string;
  primary_model: string;
  secondary_model: string;
  primary_final_score: number;
  secondary_final_score: number;
  agreement?: boolean | null;
  agreement_delta?: number | null;
  secondary_output_json: Record<string, unknown>;
  reviewed_at: string;
};

import { UUID } from "./common";

export type ReviewType = "entity_resolution" | "high_impact_event";

export type ReviewStatus = "pending" | "resolved" | "rejected";

export type ReviewItem = {
  id: UUID;
  review_type: ReviewType;
  status: ReviewStatus;
  subject_json: Record<string, unknown>;
  candidates_json: unknown[];
  resolution_json?: Record<string, unknown> | null;
  created_at: string;
  resolved_at?: string | null;
  resolved_by?: string | null;
};

export type ResolveReviewItemRequest = {
  resolved_actor_id: UUID;
};

export type AcknowledgeReviewItemRequest = {
  note?: string | null;
};

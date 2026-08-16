import { LifecycleStatus, UUID, VerificationStatus } from "./common";

export type EvidenceStance = "supports" | "refutes" | "neutral" | "context";

export type ClaimEvidence = {
  id: UUID;
  document_id: UUID;
  chunk_id?: UUID | null;
  stance: EvidenceStance;
  excerpt: string;
  source_location?: string | null;
  confidence?: number | null;
  analyst_note?: string | null;
  created_at: string;
};

export type Claim = {
  id: UUID;
  claim_text: string;
  claim_type: string;
  claimant_actor_id?: UUID | null;
  subject_actor_id?: UUID | null;
  event_id?: UUID | null;
  verification_status: VerificationStatus;
  lifecycle_status: LifecycleStatus;
  confidence?: number | null;
};

export type CreateClaimRequest = {
  claim_text: string;
  claim_type: string;
  claimant_actor_id?: UUID | null;
  subject_actor_id?: UUID | null;
  event_id?: UUID | null;
};

export type AddClaimEvidenceRequest = {
  document_id: UUID;
  stance: EvidenceStance;
  excerpt: string;
  chunk_id?: UUID | null;
  source_location?: string | null;
  confidence?: number | null;
  analyst_note?: string | null;
};

export type UpdateClaimRequest = {
  claim_text?: string;
  claim_type?: string;
  verification_status?: VerificationStatus;
  lifecycle_status?: LifecycleStatus;
  confidence?: number | null;
};


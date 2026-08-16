import { UUID, VerificationStatus } from "./common";

export type ImageEvidence = {
  id: UUID;
  source_id?: UUID | null;
  document_id?: UUID | null;
  content_type: string;
  content_hash: string;
  captured_at?: string | null;
  retrieved_at: string;
  latitude?: number | null;
  longitude?: number | null;
  location_precision?: string | null;
  caption?: string | null;
  verification_status: VerificationStatus;
  confidence?: number | null;
  analysis: Record<string, unknown>;
};

export type SubmitImageRequest = {
  image_url: string;
  source_id?: UUID | null;
  document_id?: UUID | null;
  caption?: string | null;
  captured_at?: string | null;
};

export type LinkImageToBundleRequest = {
  bundle_id: UUID;
  weight?: number;
};

export type UpdateImageRequest = {
  caption?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  verification_status?: VerificationStatus;
};


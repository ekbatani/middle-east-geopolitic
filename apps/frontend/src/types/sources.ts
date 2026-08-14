import { UUID } from "./common";

export type SourceType =
  | "rss"
  | "telegram"
  | "official_statement"
  | "think_tank"
  | "social_media"
  | "satellite"
  | "manual";

export type DocumentStatus = "raw" | "parsed" | "extracted" | "embedded" | "failed";

export type Source = {
  id: UUID;
  name: string;
  source_type: SourceType;
  base_url?: string | null;
  enabled: boolean;
};

export type SubmitSourceRequest = {
  url: string;
  title?: string | null;
  source_id?: UUID | null;
};

export type SubmitSourceResponse = {
  document_id: UUID;
  source_id: UUID;
  status: DocumentStatus;
  canonical_url: string;
  title?: string | null;
  extracted_text_preview?: string | null;
};

export type DocumentChunk = {
  id: UUID;
  sequence: number;
  text: string;
  token_count?: number | null;
};

export type Document = {
  id: UUID;
  source_id: UUID;
  canonical_url: string;
  title?: string | null;
  status: DocumentStatus;
  content_hash?: string | null;
  retrieved_at?: string | null;
  extracted_text?: string | null;
  chunks: DocumentChunk[];
};

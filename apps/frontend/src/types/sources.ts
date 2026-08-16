import { UUID } from "./common";

export type SourceType =
  | "news_outlet"
  | "state_media"
  | "wire_service"
  | "government"
  | "think_tank"
  | "ngo"
  | "academic"
  | "social_media"
  | "satellite"
  | "telegram"
  | "official_statement"
  | "other"
  | "rss"
  | "manual";

export type EndpointType = "rss" | "html" | "api" | "scraper" | "telegram";

export type DocumentStatus = "raw" | "parsed" | "extracted" | "embedded" | "failed";

export type SourceEndpoint = {
  id: UUID;
  source_id: UUID;
  endpoint_type: EndpointType;
  url: string;
  schedule?: string | null;
  parser_name?: string | null;
  priority: number;
  last_success_at?: string | null;
  last_failure_at?: string | null;
  failure_count: number;
};

export type Source = {
  id: UUID;
  name: string;
  source_type: SourceType;
  base_url?: string | null;
  jurisdiction?: string | null;
  default_language?: string | null;
  enabled: boolean;
  endpoints?: SourceEndpoint[];
};

export type CreateSourceRequest = {
  name: string;
  source_type: SourceType;
  base_url?: string | null;
  default_language?: string | null;
  jurisdiction?: string | null;
};

export type UpdateSourceRequest = {
  name?: string;
  source_type?: SourceType;
  base_url?: string | null;
  default_language?: string | null;
  enabled?: boolean;
};

export type CreateSourceEndpointRequest = {
  endpoint_type: EndpointType;
  url: string;
  schedule?: string | null;
  priority?: number;
};

export type UpdateSourceEndpointRequest = {
  endpoint_type?: EndpointType;
  url?: string;
  schedule?: string | null;
  priority?: number;
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

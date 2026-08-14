import { ScopeType, UUID } from "./common";

export type IndicatorNormalizationMethod =
  | "min_max"
  | "z_score"
  | "sigmoid"
  | "step"
  | "log"
  | "linear_bounded";

export type IndicatorDefinition = {
  id: UUID;
  code: string;
  name: string;
  description?: string | null;
  category: string;
  value_type: string;
  normalization_method: IndicatorNormalizationMethod;
  lower_bound?: number | null;
  upper_bound?: number | null;
  staleness_hours?: number | null;
  active: boolean;
};

export type IndicatorObservation = {
  id: UUID;
  indicator_id: UUID;
  scope_type: ScopeType;
  scope_id: UUID;
  observed_at: string;
  raw_value: number;
  normalized_value: number;
  confidence: number;
  source_method?: string | null;
};

export type RecordObservationRequest = {
  scope_type: ScopeType;
  scope_id: UUID;
  raw_value: number;
  confidence?: number;
  observed_at?: string | null;
  source_method?: string | null;
};

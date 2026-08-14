import { UUID } from "./common";

export type ForecastStatus = "active" | "resolved" | "cancelled";

export type ForecastOutcome = "occurred" | "did_not_occur" | "ambiguous";

export type Forecast = {
  id: UUID;
  question: string;
  issued_at: string;
  resolution_date: string;
  probability: number;
  confidence: number;
  assumptions: string[];
  evidence_bundle_id?: UUID | null;
  status: ForecastStatus;
  outcome?: ForecastOutcome | null;
  resolved_at?: string | null;
  brier_score?: number | null;
  evaluation_note?: string | null;
};

export type IssueForecastRequest = {
  question: string;
  resolution_date: string;
  probability: number;
  confidence: number;
  assumptions?: string[];
  evidence_bundle_id?: UUID | null;
};

export type ResolveForecastRequest = {
  outcome: ForecastOutcome;
  evaluation_note?: string | null;
};

export type CalibrationBucket = {
  lower: number;
  upper: number;
  forecast_count: number;
  mean_predicted_probability?: number | null;
  observed_frequency?: number | null;
  mean_brier_score?: number | null;
};

export type CalibrationReport = {
  overall_brier_score?: number | null;
  resolved_count: number;
  open_count: number;
  buckets: CalibrationBucket[];
};

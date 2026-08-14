import { UUID } from "./common";

export type InvestigationStep = {
  id: UUID;
  step_type: string;
  sequence: number;
  status: string;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
};

export type Investigation = {
  id: UUID;
  title: string;
  question: string;
  status: string;
  priority: string;
  requested_by: string;
  assigned_to?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  result_summary?: string | null;
  confidence?: number | null;
  report_id?: UUID | null;
  created_at: string;
  updated_at: string;
};

export type InvestigationDetail = Investigation & {
  steps: InvestigationStep[];
};

export type CreateInvestigationRequest = {
  title: string;
  question: string;
  priority?: string;
  assigned_to?: string | null;
};

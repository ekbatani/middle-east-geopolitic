import { ScopeType, UUID } from "./common";

export type ReportType = "daily_brief" | "weekly_brief" | "country_brief" | "conflict_brief" | "investigation_report";

export type ReportStatus = "draft" | "under_review" | "approved" | "rejected" | "published";

export type Report = {
  id: UUID;
  report_type: ReportType;
  title: string;
  scope_type?: ScopeType | null;
  scope_id?: UUID | null;
  period_start?: string | null;
  period_end?: string | null;
  content_markdown: string;
  content_object_key?: string | null;
  status: ReportStatus;
  generated_by_model?: string | null;
  prompt_version?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  published_at?: string | null;
};

export type ReportSummary = {
  id: UUID;
  report_type: ReportType;
  title: string;
  scope_type?: ScopeType | null;
  scope_id?: UUID | null;
  period_start?: string | null;
  period_end?: string | null;
  status: ReportStatus;
  published_at?: string | null;
};

export type GenerateReportRequest = {
  report_type: ReportType;
  scope_type?: ScopeType | null;
  scope_id?: UUID | null;
};

export type UpdateReportRequest = {
  title?: string;
  content_markdown?: string;
  status?: ReportStatus;
};


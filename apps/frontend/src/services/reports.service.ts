import { apiClient } from "./client";
import {
  GenerateReportRequest,
  PaginationParams,
  Report,
  ReportStatus,
  ReportSummary,
  ReportType,
  ScopeType,
  UpdateReportRequest,
  UUID,
} from "../types";

export type ListReportsParams = PaginationParams & {
  report_type?: ReportType;
  scope_type?: ScopeType;
  scope_id?: UUID;
  status?: ReportStatus;
};

export const reportsService = {
  async listReports(params?: ListReportsParams): Promise<ReportSummary[]> {
    return apiClient.get<ReportSummary[]>("/api/v1/reports", params);
  },

  async getReport(reportId: UUID): Promise<Report> {
    return apiClient.get<Report>(`/api/v1/reports/${reportId}`);
  },

  async generateReport(payload: GenerateReportRequest): Promise<Report> {
    return apiClient.post<Report>("/api/v1/reports/generate", payload);
  },

  async updateReport(reportId: UUID, payload: UpdateReportRequest): Promise<Report> {
    return apiClient.patch<Report>(`/api/v1/reports/${reportId}`, payload);
  },

  async deleteReport(reportId: UUID): Promise<void> {
    return apiClient.delete<void>(`/api/v1/reports/${reportId}`);
  },

  async approveReport(reportId: UUID): Promise<Report> {
    return apiClient.post<Report>(`/api/v1/reports/${reportId}/approve`);
  },

  async rejectReport(reportId: UUID): Promise<Report> {
    return apiClient.post<Report>(`/api/v1/reports/${reportId}/reject`);
  },

  async publishReport(reportId: UUID): Promise<Report> {
    return apiClient.post<Report>(`/api/v1/reports/${reportId}/publish`);
  },
};

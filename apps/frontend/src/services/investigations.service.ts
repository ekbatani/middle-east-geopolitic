import { apiClient } from "./client";
import {
  CreateInvestigationRequest,
  Investigation,
  InvestigationDetail,
  PaginationParams,
  UpdateInvestigationRequest,
  UUID,
} from "../types";

export type ListInvestigationsParams = PaginationParams & {
  status?: string;
  priority?: string;
};

export const investigationsService = {
  async listInvestigations(params?: ListInvestigationsParams): Promise<Investigation[]> {
    return apiClient.get<Investigation[]>("/api/v1/investigations", params);
  },

  async getInvestigation(investigationId: UUID): Promise<InvestigationDetail> {
    return apiClient.get<InvestigationDetail>(`/api/v1/investigations/${investigationId}`);
  },

  async createInvestigation(payload: CreateInvestigationRequest): Promise<Investigation> {
    return apiClient.post<Investigation>("/api/v1/investigations", payload);
  },

  async updateInvestigation(
    investigationId: UUID,
    payload: UpdateInvestigationRequest
  ): Promise<Investigation> {
    return apiClient.patch<Investigation>(`/api/v1/investigations/${investigationId}`, payload);
  },

  async deleteInvestigation(investigationId: UUID): Promise<void> {
    return apiClient.delete<void>(`/api/v1/investigations/${investigationId}`);
  },
};

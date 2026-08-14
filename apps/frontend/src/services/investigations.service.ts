import { apiClient } from "./client";
import {
  CreateInvestigationRequest,
  Investigation,
  InvestigationDetail,
  PaginationParams,
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
};

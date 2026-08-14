import { apiClient } from "./client";
import {
  PaginationParams,
  RecalculateRiskRequest,
  RiskAssessment,
  RiskCatalogItem,
  ScopeType,
  UUID,
} from "../types";

export type ListRisksParams = {
  scope_type?: ScopeType;
  scope_id?: UUID;
};

export type RiskHistoryParams = PaginationParams & {
  scope_type: ScopeType;
  scope_id?: UUID;
  since?: string;
  until?: string;
};

export const risksService = {
  async listRisks(params?: ListRisksParams): Promise<RiskCatalogItem[]> {
    return apiClient.get<RiskCatalogItem[]>("/api/v1/risks", params);
  },

  async getRiskHistory(
    riskDefinitionId: UUID,
    params: RiskHistoryParams
  ): Promise<RiskAssessment[]> {
    return apiClient.get<RiskAssessment[]>(
      `/api/v1/risks/${riskDefinitionId}/history`,
      params
    );
  },

  async recalculateRisk(payload: RecalculateRiskRequest): Promise<RiskAssessment> {
    return apiClient.post<RiskAssessment>("/api/v1/risks/recalculate", payload);
  },
};

import { apiClient } from "./client";
import {
  IndicatorDefinition,
  IndicatorObservation,
  PaginationParams,
  RecordObservationRequest,
  ScopeType,
  UUID,
} from "../types";

export type ListIndicatorObservationsParams = PaginationParams & {
  scope_type: ScopeType;
  scope_id: UUID;
};

export const indicatorsService = {
  async listIndicators(activeOnly = true): Promise<IndicatorDefinition[]> {
    return apiClient.get<IndicatorDefinition[]>("/api/v1/indicators", { active_only: activeOnly });
  },

  async listObservations(
    indicatorCode: string,
    params: ListIndicatorObservationsParams
  ): Promise<IndicatorObservation[]> {
    return apiClient.get<IndicatorObservation[]>(
      `/api/v1/indicators/${indicatorCode}/observations`,
      params
    );
  },

  async recordObservation(
    indicatorCode: string,
    payload: RecordObservationRequest
  ): Promise<IndicatorObservation> {
    return apiClient.post<IndicatorObservation>(
      `/api/v1/indicators/${indicatorCode}/observations`,
      payload
    );
  },
};

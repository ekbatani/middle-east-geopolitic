import { apiClient } from "./client";
import {
  AnalystAssessment,
  DisagreementSubjectType,
  DisagreementSummary,
  PaginationParams,
  RecordPositionRequest,
  UUID,
} from "../types";

export type ListPositionsParams = {
  subject_type: DisagreementSubjectType;
  subject_id: UUID;
};

export type ListDisagreementsParams = PaginationParams & {
  subject_type?: DisagreementSubjectType;
  score_spread_threshold?: number;
};

export const analystService = {
  async recordPosition(payload: RecordPositionRequest): Promise<AnalystAssessment> {
    return apiClient.post<AnalystAssessment>("/api/v1/analyst-assessments", payload);
  },

  async listPositions(params: ListPositionsParams): Promise<AnalystAssessment[]> {
    return apiClient.get<AnalystAssessment[]>("/api/v1/analyst-assessments", params);
  },

  async listDisagreements(params?: ListDisagreementsParams): Promise<DisagreementSummary[]> {
    return apiClient.get<DisagreementSummary[]>("/api/v1/analyst-assessments/disagreements", params);
  },
};

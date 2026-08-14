import { apiClient } from "./client";
import {
  PaginationParams,
  Source,
  SubmitSourceRequest,
  SubmitSourceResponse,
  UUID,
} from "../types";

export const sourcesService = {
  async listSources(params?: PaginationParams): Promise<Source[]> {
    return apiClient.get<Source[]>("/api/v1/sources", params);
  },

  async getSource(sourceId: UUID): Promise<Source> {
    return apiClient.get<Source>(`/api/v1/sources/${sourceId}`);
  },

  async submitSource(payload: SubmitSourceRequest): Promise<SubmitSourceResponse> {
    return apiClient.post<SubmitSourceResponse>("/api/v1/sources/submit", payload);
  },
};

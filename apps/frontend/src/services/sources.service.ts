import { apiClient } from "./client";
import {
  CreateSourceEndpointRequest,
  CreateSourceRequest,
  PaginationParams,
  Source,
  SourceEndpoint,
  SubmitSourceRequest,
  SubmitSourceResponse,
  UpdateSourceEndpointRequest,
  UpdateSourceRequest,
  UUID,
} from "../types";

export const sourcesService = {
  async listSources(params?: PaginationParams): Promise<Source[]> {
    return apiClient.get<Source[]>("/api/v1/sources", params);
  },

  async getSource(sourceId: UUID): Promise<Source> {
    return apiClient.get<Source>(`/api/v1/sources/${sourceId}`);
  },

  async createSource(payload: CreateSourceRequest): Promise<Source> {
    return apiClient.post<Source>("/api/v1/sources", payload);
  },

  async updateSource(sourceId: UUID, payload: UpdateSourceRequest): Promise<Source> {
    return apiClient.patch<Source>(`/api/v1/sources/${sourceId}`, payload);
  },

  async deleteSource(sourceId: UUID): Promise<void> {
    return apiClient.delete<void>(`/api/v1/sources/${sourceId}`);
  },

  async addSourceEndpoint(sourceId: UUID, payload: CreateSourceEndpointRequest): Promise<SourceEndpoint> {
    return apiClient.post<SourceEndpoint>(`/api/v1/sources/${sourceId}/endpoints`, payload);
  },

  async updateSourceEndpoint(endpointId: UUID, payload: UpdateSourceEndpointRequest): Promise<SourceEndpoint> {
    return apiClient.patch<SourceEndpoint>(`/api/v1/sources/endpoints/${endpointId}`, payload);
  },

  async deleteSourceEndpoint(endpointId: UUID): Promise<void> {
    return apiClient.delete<void>(`/api/v1/sources/endpoints/${endpointId}`);
  },

  async submitSource(payload: SubmitSourceRequest): Promise<SubmitSourceResponse> {
    return apiClient.post<SubmitSourceResponse>("/api/v1/sources/submit", payload);
  },
};

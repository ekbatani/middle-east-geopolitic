import { apiClient } from "./client";
import {
  CreateMonitorRequest,
  Monitor,
  PaginationParams,
  UpdateMonitorRequest,
  UUID,
} from "../types";

export type ListMonitorsParams = PaginationParams & {
  enabled?: boolean;
};

export const monitorsService = {
  async listMonitors(params?: ListMonitorsParams): Promise<Monitor[]> {
    return apiClient.get<Monitor[]>("/api/v1/monitors", params);
  },

  async getMonitor(monitorId: UUID): Promise<Monitor> {
    return apiClient.get<Monitor>(`/api/v1/monitors/${monitorId}`);
  },

  async createMonitor(payload: CreateMonitorRequest): Promise<Monitor> {
    return apiClient.post<Monitor>("/api/v1/monitors", payload);
  },

  async updateMonitor(monitorId: UUID, payload: UpdateMonitorRequest): Promise<Monitor> {
    return apiClient.patch<Monitor>(`/api/v1/monitors/${monitorId}`, payload);
  },

  async deleteMonitor(monitorId: UUID): Promise<void> {
    return apiClient.delete<void>(`/api/v1/monitors/${monitorId}`);
  },
};

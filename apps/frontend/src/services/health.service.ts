import { apiClient } from "./client";
import { HealthStatus } from "../types";

export const healthService = {
  async checkLive(): Promise<HealthStatus> {
    return apiClient.get<HealthStatus>("/health/live");
  },

  async checkReady(): Promise<HealthStatus> {
    return apiClient.get<HealthStatus>("/health/ready");
  },

  async checkDependencies(): Promise<HealthStatus> {
    return apiClient.get<HealthStatus>("/health/dependencies");
  },
};

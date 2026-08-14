import { apiClient } from "./client";
import {
  CalibrationReport,
  Forecast,
  ForecastStatus,
  IssueForecastRequest,
  PaginationParams,
  ResolveForecastRequest,
  UUID,
} from "../types";

export type ListForecastsParams = PaginationParams & {
  status?: ForecastStatus;
};

export type CalibrationParams = {
  since?: string;
  until?: string;
  bucket_count?: number;
};

export const forecastsService = {
  async listForecasts(params?: ListForecastsParams): Promise<Forecast[]> {
    return apiClient.get<Forecast[]>("/api/v1/forecasts", params);
  },

  async getForecast(forecastId: UUID): Promise<Forecast> {
    return apiClient.get<Forecast>(`/api/v1/forecasts/${forecastId}`);
  },

  async issueForecast(payload: IssueForecastRequest): Promise<Forecast> {
    return apiClient.post<Forecast>("/api/v1/forecasts", payload);
  },

  async resolveForecast(forecastId: UUID, payload: ResolveForecastRequest): Promise<Forecast> {
    return apiClient.post<Forecast>(`/api/v1/forecasts/${forecastId}/resolve`, payload);
  },

  async getCalibration(params?: CalibrationParams): Promise<CalibrationReport> {
    return apiClient.get<CalibrationReport>("/api/v1/forecasts/calibration", params);
  },
};

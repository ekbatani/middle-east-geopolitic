import { apiClient } from "./client";
import {
  CreateScenarioRequest,
  PaginationParams,
  Scenario,
  ScenarioAssessment,
  ScenarioSimulationRequest,
  ScenarioStatus,
  ScenarioUpdateRecommendation,
  ScopeType,
  UUID,
} from "../types";

export type ListScenariosParams = {
  scope_type?: ScopeType;
  scope_id?: UUID;
  status?: ScenarioStatus;
};

export type ScenarioHistoryParams = PaginationParams & {
  since?: string;
  until?: string;
};

export const scenariosService = {
  async listScenarios(params?: ListScenariosParams): Promise<Scenario[]> {
    return apiClient.get<Scenario[]>("/api/v1/scenarios", params);
  },

  async getScenario(scenarioId: UUID): Promise<Scenario> {
    return apiClient.get<Scenario>(`/api/v1/scenarios/${scenarioId}`);
  },

  async getScenarioHistory(
    scenarioId: UUID,
    params?: ScenarioHistoryParams
  ): Promise<ScenarioAssessment[]> {
    return apiClient.get<ScenarioAssessment[]>(
      `/api/v1/scenarios/${scenarioId}/history`,
      params
    );
  },

  async createScenario(payload: CreateScenarioRequest): Promise<Scenario> {
    return apiClient.post<Scenario>("/api/v1/scenarios", payload);
  },

  async updateScenario(scenarioId: UUID): Promise<ScenarioAssessment> {
    return apiClient.post<ScenarioAssessment>(`/api/v1/scenarios/${scenarioId}/update`);
  },

  async simulateScenario(
    payload: ScenarioSimulationRequest
  ): Promise<ScenarioUpdateRecommendation> {
    return apiClient.post<ScenarioUpdateRecommendation>("/api/v1/scenarios/simulate", payload);
  },
};

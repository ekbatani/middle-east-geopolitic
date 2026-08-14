import { apiClient } from "./client";
import {
  CountryBriefRequest,
  CountryBriefResponse,
  EventInvestigationRequest,
  IntelligenceSearchRequest,
  MapEvent,
  PaginationParams,
  RelationshipComparisonItem,
  RelationshipComparisonRequest,
  Report,
  RiskExplanation,
  ScenarioSimulationRequest,
  ScenarioUpdateRecommendation,
  SearchItem,
  UUID,
} from "../types";

export type MapEventsParams = PaginationParams & {
  bbox?: string;
  since?: string;
  until?: string;
  event_type?: string;
  min_severity?: number;
  country_actor_id?: UUID;
};

export const intelligenceService = {
  async search(query: string, limit = 50): Promise<SearchItem[]> {
    return apiClient.post<SearchItem[]>("/api/v1/intelligence/search", { query, limit });
  },

  async getCountryBrief(payload: CountryBriefRequest): Promise<CountryBriefResponse> {
    return apiClient.post<CountryBriefResponse>("/api/v1/intelligence/country-brief", payload);
  },

  async compareRelationships(
    payload: RelationshipComparisonRequest
  ): Promise<RelationshipComparisonItem[]> {
    return apiClient.post<RelationshipComparisonItem[]>(
      "/api/v1/intelligence/relationship-comparison",
      payload
    );
  },

  async getRiskExplanation(payload: {
    risk_definition_id: UUID;
    scope_type: string;
    scope_id?: UUID | null;
    as_of?: string | null;
  }): Promise<RiskExplanation> {
    return apiClient.post<RiskExplanation>("/api/v1/intelligence/risk-explanation", payload);
  },

  async getDailyBrief(): Promise<Report> {
    return apiClient.post<Report>("/api/v1/intelligence/daily-brief");
  },

  async simulateScenario(
    payload: ScenarioSimulationRequest
  ): Promise<ScenarioUpdateRecommendation> {
    return apiClient.post<ScenarioUpdateRecommendation>(
      "/api/v1/intelligence/scenario-simulation",
      payload
    );
  },

  async launchEventInvestigation(
    payload: EventInvestigationRequest
  ): Promise<{ investigation_id: UUID; status: string; title: string }> {
    return apiClient.post<{ investigation_id: UUID; status: string; title: string }>(
      "/api/v1/intelligence/event-investigation",
      payload
    );
  },

  async getMapEvents(params?: MapEventsParams): Promise<MapEvent[]> {
    return apiClient.get<MapEvent[]>("/api/v1/intelligence/map-events", params);
  },
};

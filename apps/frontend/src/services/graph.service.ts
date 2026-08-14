import { apiClient } from "./client";
import {
  ActorCentrality,
  GraphCommunity,
  GraphPath,
  GraphSnapshot,
  RelationshipStatus,
  UUID,
} from "../types";

export type GraphParams = {
  relationship_status?: RelationshipStatus;
};

export type ShortestPathParams = GraphParams & {
  source_actor_id: UUID;
  target_actor_id: UUID;
};

export const graphService = {
  async getSnapshot(params?: GraphParams): Promise<GraphSnapshot> {
    return apiClient.get<GraphSnapshot>("/api/v1/graph/snapshot", params);
  },

  async getCentrality(params?: GraphParams): Promise<ActorCentrality[]> {
    return apiClient.get<ActorCentrality[]>("/api/v1/graph/centrality", params);
  },

  async getShortestPath(params: ShortestPathParams): Promise<GraphPath> {
    return apiClient.get<GraphPath>("/api/v1/graph/path", params);
  },

  async getCommunities(params?: GraphParams): Promise<GraphCommunity[]> {
    return apiClient.get<GraphCommunity[]>("/api/v1/graph/communities", params);
  },
};

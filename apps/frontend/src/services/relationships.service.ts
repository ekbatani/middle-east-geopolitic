import { apiClient } from "./client";
import {
  AssessRelationshipRequest,
  CreateRelationshipRequest,
  PaginationParams,
  Relationship,
  RelationshipObservation,
  RelationshipStatus,
  UUID,
} from "../types";

export type ListRelationshipsParams = PaginationParams & {
  actor_id?: UUID;
  relationship_type?: string;
  status?: RelationshipStatus;
};

export type RelationshipHistoryParams = PaginationParams & {
  since?: string;
  until?: string;
};

export const relationshipsService = {
  async listRelationships(params?: ListRelationshipsParams): Promise<Relationship[]> {
    return apiClient.get<Relationship[]>("/api/v1/relationships", params);
  },

  async getRelationship(relationshipId: UUID): Promise<Relationship> {
    return apiClient.get<Relationship>(`/api/v1/relationships/${relationshipId}`);
  },

  async getRelationshipHistory(
    relationshipId: UUID,
    params?: RelationshipHistoryParams
  ): Promise<RelationshipObservation[]> {
    return apiClient.get<RelationshipObservation[]>(
      `/api/v1/relationships/${relationshipId}/history`,
      params
    );
  },

  async createRelationship(payload: CreateRelationshipRequest): Promise<Relationship> {
    return apiClient.post<Relationship>("/api/v1/relationships", payload);
  },

  async assessRelationship(
    relationshipId: UUID,
    payload: AssessRelationshipRequest
  ): Promise<RelationshipObservation> {
    return apiClient.post<RelationshipObservation>(
      `/api/v1/relationships/${relationshipId}/assess`,
      payload
    );
  },
};

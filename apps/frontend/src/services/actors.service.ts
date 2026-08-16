import { apiClient } from "./client";
import {
  Actor,
  ActorAlias,
  ActorTimelineResponse,
  ActorType,
  CreateActorAliasRequest,
  CreateActorRequest,
  PaginationParams,
  UpdateActorRequest,
  UUID,
} from "../types";

export type ListActorsParams = PaginationParams & {
  q?: string;
  actor_type?: ActorType;
};

export const actorsService = {
  async listActors(params?: ListActorsParams): Promise<Actor[]> {
    return apiClient.get<Actor[]>("/api/v1/actors", params);
  },

  async getActor(actorId: UUID): Promise<Actor> {
    return apiClient.get<Actor>(`/api/v1/actors/${actorId}`);
  },

  async getActorTimeline(actorId: UUID): Promise<ActorTimelineResponse> {
    return apiClient.get<ActorTimelineResponse>(`/api/v1/actors/${actorId}/timeline`);
  },

  async createActor(payload: CreateActorRequest): Promise<Actor> {
    return apiClient.post<Actor>("/api/v1/actors", payload);
  },

  async updateActor(actorId: UUID, payload: UpdateActorRequest): Promise<Actor> {
    return apiClient.patch<Actor>(`/api/v1/actors/${actorId}`, payload);
  },

  async deleteActor(actorId: UUID): Promise<void> {
    return apiClient.delete<void>(`/api/v1/actors/${actorId}`);
  },

  async addActorAlias(actorId: UUID, payload: CreateActorAliasRequest): Promise<ActorAlias> {
    return apiClient.post<ActorAlias>(`/api/v1/actors/${actorId}/aliases`, payload);
  },

  async deleteActorAlias(actorId: UUID, aliasId: UUID): Promise<void> {
    return apiClient.delete<void>(`/api/v1/actors/${actorId}/aliases/${aliasId}`);
  },
};

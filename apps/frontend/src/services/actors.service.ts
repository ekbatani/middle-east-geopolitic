import { apiClient } from "./client";
import {
  Actor,
  ActorAlias,
  ActorTimelineResponse,
  ActorType,
  CreateActorAliasRequest,
  CreateActorRequest,
  PaginationParams,
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

  async addActorAlias(actorId: UUID, payload: CreateActorAliasRequest): Promise<ActorAlias> {
    return apiClient.post<ActorAlias>(`/api/v1/actors/${actorId}/aliases`, payload);
  },
};

import { apiClient } from "./client";
import {
  AddEventActorRequest,
  AddEventImpactRequest,
  AddEventLocationRequest,
  CreateEventRequest,
  Event,
  EventActor,
  EventImpact,
  EventLocation,
  LifecycleStatus,
  PaginationParams,
  UUID,
} from "../types";

export type ListEventsParams = PaginationParams & {
  lifecycle_status?: LifecycleStatus;
  event_type?: string;
};

export const eventsService = {
  async listEvents(params?: ListEventsParams): Promise<Event[]> {
    return apiClient.get<Event[]>("/api/v1/events", params);
  },

  async getEvent(eventId: UUID): Promise<Event> {
    return apiClient.get<Event>(`/api/v1/events/${eventId}`);
  },

  async createEvent(payload: CreateEventRequest): Promise<Event> {
    return apiClient.post<Event>("/api/v1/events", payload);
  },

  async addActor(eventId: UUID, payload: AddEventActorRequest): Promise<EventActor> {
    return apiClient.post<EventActor>(`/api/v1/events/${eventId}/actors`, payload);
  },

  async addLocation(eventId: UUID, payload: AddEventLocationRequest): Promise<EventLocation> {
    return apiClient.post<EventLocation>(`/api/v1/events/${eventId}/locations`, payload);
  },

  async addImpact(eventId: UUID, payload: AddEventImpactRequest): Promise<EventImpact> {
    return apiClient.post<EventImpact>(`/api/v1/events/${eventId}/impacts`, payload);
  },

  async approveEvent(eventId: UUID): Promise<Event> {
    return apiClient.post<Event>(`/api/v1/events/${eventId}/approve`);
  },

  async rejectEvent(eventId: UUID): Promise<Event> {
    return apiClient.post<Event>(`/api/v1/events/${eventId}/reject`);
  },
};

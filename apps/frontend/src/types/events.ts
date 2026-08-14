import { LifecycleStatus, UUID, VerificationStatus } from "./common";

export type EventActor = {
  actor_id: UUID;
  role: string;
  participation_status?: string | null;
  confidence?: number | null;
};

export type EventLocation = {
  id: UUID;
  name: string;
  country_actor_id?: UUID | null;
  latitude?: number | null;
  longitude?: number | null;
  location_precision?: string | null;
};

export type EventImpact = {
  id: UUID;
  impact_type: string;
  magnitude?: number | null;
  unit?: string | null;
  estimate_low?: number | null;
  estimate_high?: number | null;
  confidence?: number | null;
};

export type Event = {
  id: UUID;
  event_type: string;
  title: string;
  summary?: string | null;
  started_at: string;
  ended_at?: string | null;
  severity?: number | null;
  strategic_significance?: string | null;
  verification_status: VerificationStatus;
  lifecycle_status: LifecycleStatus;
  confidence?: number | null;
  actors: EventActor[];
  locations: EventLocation[];
  impacts: EventImpact[];
};

export type CreateEventRequest = {
  event_type: string;
  title: string;
  started_at: string;
  summary?: string | null;
  ended_at?: string | null;
  time_precision?: string | null;
  severity?: number | null;
  strategic_significance?: string | null;
};

export type AddEventActorRequest = {
  actor_id: UUID;
  role: string;
  participation_status?: string | null;
  confidence?: number | null;
};

export type AddEventLocationRequest = {
  name: string;
  country_actor_id?: UUID | null;
  latitude?: number | null;
  longitude?: number | null;
  location_precision?: string | null;
};

export type AddEventImpactRequest = {
  impact_type: string;
  magnitude?: number | null;
  unit?: string | null;
  estimate_low?: number | null;
  estimate_high?: number | null;
  confidence?: number | null;
};

export type MapEventLocation = {
  name: string;
  latitude?: number | null;
  longitude?: number | null;
  location_precision?: string | null;
  country_actor_id?: UUID | null;
};

export type MapEvent = {
  event_id: UUID;
  title: string;
  event_type: string;
  started_at: string;
  severity?: number | null;
  strategic_significance?: string | null;
  verification_status: string;
  locations: MapEventLocation[];
};

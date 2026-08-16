import { UUID } from "./common";

export type ActorType =
  | "country"
  | "state_leader"
  | "armed_non_state"
  | "political_party"
  | "organization"
  | "coalition"
  | "person";

export type ActorStatus = "active" | "inactive" | "dissolved" | "deceased";

export type ActorAlias = {
  id: UUID;
  alias: string;
  language?: string | null;
  alias_type?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
};

export type Actor = {
  id: UUID;
  canonical_name: string;
  native_name?: string | null;
  actor_type: ActorType;
  status: ActorStatus;
  parent_actor_id?: UUID | null;
  country_actor_id?: UUID | null;
  description?: string | null;
  aliases: ActorAlias[];
};

export type ActorLeadership = {
  id: UUID;
  person_actor_id: UUID;
  role_name: string;
  valid_from?: string | null;
  valid_to?: string | null;
};

export type ActorTimelineResponse = {
  actor_id: UUID;
  leadership: ActorLeadership[];
};

export type CreateActorRequest = {
  canonical_name: string;
  actor_type: ActorType;
  native_name?: string | null;
  parent_actor_id?: UUID | null;
  country_actor_id?: UUID | null;
  description?: string | null;
};

export type CreateActorAliasRequest = {
  alias: string;
  language?: string | null;
  alias_type?: string | null;
};

export type UpdateActorRequest = {
  canonical_name?: string;
  actor_type?: ActorType;
  native_name?: string | null;
  description?: string | null;
  status?: ActorStatus;
};


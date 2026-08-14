import { UUID } from "./common";

export type Monitor = {
  id: UUID;
  name: string;
  user_id: UUID;
  monitor_type: string;
  condition_json: Record<string, unknown>;
  schedule?: string | null;
  delivery_channel: string;
  enabled: boolean;
  last_evaluated_at?: string | null;
  last_triggered_at?: string | null;
};

export type CreateMonitorRequest = {
  name: string;
  monitor_type: string;
  condition_json: Record<string, unknown>;
  schedule?: string | null;
  delivery_channel?: string;
  enabled?: boolean;
};

export type UpdateMonitorRequest = {
  name?: string;
  condition_json?: Record<string, unknown>;
  schedule?: string | null;
  delivery_channel?: string;
  enabled?: boolean;
};

export type JobExecution = {
  id: string;
  schedule_id: string | null;
  job_type: string;
  started_at: string;
  completed_at: string | null;
  status: "running" | "success" | "failed";
  items_processed: number;
  error_message: string | null;
  log_output: string | null;
};

export type JobSchedule = {
  id: string;
  name: string;
  job_type: string;
  cron_expression: string | null;
  interval_seconds: number | null;
  parameters: Record<string, unknown>;
  enabled: boolean;
  last_run_at: string | null;

  next_run_at: string | null;
  last_status: string | null;
  executions: JobExecution[];
};

export type CreateJobScheduleRequest = {
  name: string;
  job_type: string;
  cron_expression?: string | null;
  interval_seconds?: number | null;
  parameters?: Record<string, unknown>;
  enabled?: boolean;
};

export type UpdateJobScheduleRequest = {
  name?: string;
  cron_expression?: string | null;
  interval_seconds?: number | null;
  parameters?: Record<string, unknown>;
  enabled?: boolean;
};

export type TriggerJobResponse = {
  success: boolean;
  job_type: string;
  items_processed: number;
  log_output: string;
};

export type TestScrapeRequest = {
  url: string;
};

export type TestScrapeResponse = {
  url: string;
  title: string | null;
  extracted_text: string | null;
  chunks_count: number;
  detected_language: string | null;
  status_code: number;
};

import { apiClient } from "./client";
import {
  JobSchedule,
  JobExecution,
  CreateJobScheduleRequest,
  UpdateJobScheduleRequest,
  TriggerJobResponse,
  TestScrapeRequest,
  TestScrapeResponse,
} from "../types";

export const schedulesService = {
  async listSchedules(params?: { enabled_only?: boolean }): Promise<JobSchedule[]> {
    return apiClient.get<JobSchedule[]>("/api/v1/schedules", params);
  },

  async createSchedule(payload: CreateJobScheduleRequest): Promise<JobSchedule> {
    return apiClient.post<JobSchedule>("/api/v1/schedules", payload);
  },

  async getSchedule(id: string): Promise<JobSchedule> {
    return apiClient.get<JobSchedule>(`/api/v1/schedules/${id}`);
  },

  async updateSchedule(id: string, payload: UpdateJobScheduleRequest): Promise<JobSchedule> {
    return apiClient.patch<JobSchedule>(`/api/v1/schedules/${id}`, payload);
  },

  async deleteSchedule(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/schedules/${id}`);
  },

  async runScheduleNow(id: string): Promise<TriggerJobResponse> {
    return apiClient.post<TriggerJobResponse>(`/api/v1/schedules/${id}/run`);
  },

  async triggerJob(jobType: string): Promise<TriggerJobResponse> {
    return apiClient.post<TriggerJobResponse>(`/api/v1/schedules/trigger-job/${jobType}`);
  },

  async listExecutions(params?: {
    job_type?: string;
    schedule_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<JobExecution[]> {
    return apiClient.get<JobExecution[]>("/api/v1/schedules/executions", params);
  },

  async testScrape(payload: TestScrapeRequest): Promise<TestScrapeResponse> {
    return apiClient.post<TestScrapeResponse>("/api/v1/schedules/test-scrape", payload);
  },
};

"use client";

import React, { useState, useEffect } from "react";
import {
  JobSchedule,
  JobExecution,
  CreateJobScheduleRequest,
  UpdateJobScheduleRequest,
  TestScrapeResponse,
} from "../../types";
import { schedulesService } from "../../services";
import {
  ActivityIcon,
  CheckCircleIcon,
  GlobeIcon,
  PlayIcon,
  PlusIcon,
  RefreshCwIcon,
  SearchIcon,
  SparklesIcon,
  Trash2Icon,
  XCircleIcon,
} from "../common/Icons";
import { Card, CardHeader } from "../common/Card";
import { Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function PipelineSchedulerView() {
  const [schedules, setSchedules] = useState<JobSchedule[]>([]);
  const [executions, setExecutions] = useState<JobExecution[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<JobExecution | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Job Run state
  const [runningJobId, setRunningJobId] = useState<string | null>(null);
  const [runMessage, setRunMessage] = useState<{ text: string; success: boolean } | null>(null);

  // Create / Edit Schedule modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState<CreateJobScheduleRequest>({
    name: "",
    job_type: "daily_news_scraping",
    cron_expression: "0 6 * * *",
    interval_seconds: 86400,
    enabled: true,
  });
  const [isCreating, setIsCreating] = useState(false);

  const [editingSchedule, setEditingSchedule] = useState<JobSchedule | null>(null);
  const [editForm, setEditForm] = useState<UpdateJobScheduleRequest>({});
  const [isUpdating, setIsUpdating] = useState(false);

  // Test Scrape Bench
  const [testUrl, setTestUrl] = useState("https://www.aljazeera.com/news/middleeast/");
  const [isScraping, setIsScraping] = useState(false);
  const [testResult, setTestResult] = useState<TestScrapeResponse | null>(null);
  const [testError, setTestError] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [schedData, execData] = await Promise.all([
        schedulesService.listSchedules(),
        schedulesService.listExecutions({ limit: 30 }),
      ]);
      setSchedules(schedData);
      setExecutions(execData);
    } catch (err) {
      console.error("Scheduler fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load schedules");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 20000);
    return () => clearInterval(interval);
  }, []);

  const handleRunNow = async (schedule: JobSchedule) => {
    setRunningJobId(schedule.id);
    setRunMessage(null);
    try {
      const res = await schedulesService.runScheduleNow(schedule.id);
      setRunMessage({
        text: `Job '${schedule.name}' completed! Processed: ${res.items_processed} items.`,
        success: res.success,
      });
      fetchData();
    } catch (err) {
      setRunMessage({
        text: `Execution failed: ${err instanceof Error ? err.message : "Error"}`,
        success: false,
      });
    } finally {
      setRunningJobId(null);
    }
  };

  const handleToggleSchedule = async (schedule: JobSchedule) => {
    try {
      await schedulesService.updateSchedule(schedule.id, { enabled: !schedule.enabled });
      fetchData();
    } catch (err) {
      console.error("Toggle error:", err);
    }
  };

  const handleDeleteSchedule = async (scheduleId: string) => {
    if (!confirm("Are you sure you want to remove this scheduled pipeline job?")) return;
    try {
      await schedulesService.deleteSchedule(scheduleId);
      fetchData();
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.name.trim()) return;
    setIsCreating(true);
    try {
      await schedulesService.createSchedule(createForm);
      setIsCreateOpen(false);
      setCreateForm({
        name: "",
        job_type: "daily_news_scraping",
        cron_expression: "0 6 * * *",
        interval_seconds: 86400,
        enabled: true,
      });
      fetchData();
    } catch (err) {
      console.error("Create schedule error:", err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSchedule) return;
    setIsUpdating(true);
    try {
      await schedulesService.updateSchedule(editingSchedule.id, editForm);
      setEditingSchedule(null);
      fetchData();
    } catch (err) {
      console.error("Update schedule error:", err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleRunTestScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testUrl.trim()) return;
    setIsScraping(true);
    setTestResult(null);
    setTestError(null);
    try {
      const res = await schedulesService.testScrape({ url: testUrl.trim() });
      setTestResult(res);
    } catch (err) {
      setTestError(err instanceof Error ? err.message : "Failed to scrape target URL");
    } finally {
      setIsScraping(false);
    }
  };

  if (isLoading && schedules.length === 0) {
    return <LoadingState message="Connecting to async pipeline scheduler & job orchestrator..." />;
  }

  if (error && schedules.length === 0) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  const activeCount = schedules.filter((s) => s.enabled).length;
  const recentSuccess = executions.filter((e) => e.status === "success").length;
  const totalItemsProcessed = executions.reduce((acc, curr) => acc + curr.items_processed, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <ActivityIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Pipeline Orchestrator & Autonomous AI Schedulers
            </h2>
            <p className="text-xs text-slate-400">
              Automated daily web scraping &bull; Multimodal AI extraction &bull; Risk & scenario recalculation schedules
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchData}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCwIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            <PlusIcon className="w-4 h-4" />
            New Schedule
          </button>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Active Schedules</span>
          <div className="text-xl font-bold text-sky-400 mt-1">
            {activeCount} <span className="text-xs font-normal text-slate-500">/ {schedules.length} total</span>
          </div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Successful Runs (Recent)</span>
          <div className="text-xl font-bold text-emerald-400 mt-1">
            {recentSuccess} <span className="text-xs font-normal text-slate-500">/ {executions.length}</span>
          </div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Items Processed</span>
          <div className="text-xl font-bold text-indigo-400 mt-1">{totalItemsProcessed}</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Scheduler Loop</span>
          <div className="flex items-center gap-1.5 mt-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-bold text-emerald-400 font-mono">ACTIVE (ASYNC)</span>
          </div>
        </div>
      </div>

      {/* Notification Toast */}
      {runMessage && (
        <div
          className={`p-3 rounded-xl border flex items-center justify-between text-xs ${
            runMessage.success
              ? "bg-emerald-950/40 border-emerald-800/60 text-emerald-300"
              : "bg-rose-950/40 border-rose-800/60 text-rose-300"
          }`}
        >
          <div className="flex items-center gap-2">
            {runMessage.success ? (
              <CheckCircleIcon className="w-4 h-4 text-emerald-400" />
            ) : (
              <XCircleIcon className="w-4 h-4 text-rose-400" />
            )}
            <span>{runMessage.text}</span>
          </div>
          <button
            onClick={() => setRunMessage(null)}
            className="text-xs hover:underline text-slate-400"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Grid: Scheduled Pipelines & Live Test Bench */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Registered Scheduled Pipelines */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader
              title="Registered Pipeline Schedules"
              subtitle="Daily news scrapers, satellite sensor sync, risk calculation, and report generation"
              icon={<ActivityIcon className="w-5 h-5" />}
            />

            <div className="space-y-3">
              {schedules.map((schedule) => {
                const isRunning = runningJobId === schedule.id || schedule.last_status === "running";
                return (
                  <div
                    key={schedule.id}
                    className="p-4 bg-slate-950/70 border border-slate-800 hover:border-slate-700 rounded-xl transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div className="space-y-1.5 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-sm text-slate-100">{schedule.name}</span>
                        <Badge
                          variant={
                            schedule.last_status === "success"
                              ? "success"
                              : schedule.last_status === "failed"
                              ? "danger"
                              : schedule.last_status === "running"
                              ? "info"
                              : "neutral"
                          }
                          size="sm"
                        >
                          {schedule.last_status || "idle"}
                        </Badge>
                        <span className="text-[10px] font-mono bg-slate-900 border border-slate-800 px-2 py-0.5 rounded text-slate-400">
                          {schedule.job_type}
                        </span>
                      </div>

                      <div className="flex items-center gap-4 text-[11px] text-slate-400 font-mono">
                        <span>
                          Interval:{" "}
                          {schedule.interval_seconds
                            ? `${schedule.interval_seconds / 3600}h`
                            : schedule.cron_expression || "Daily"}
                        </span>
                        <span>
                          Last Run:{" "}
                          {schedule.last_run_at
                            ? new Date(schedule.last_run_at).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            : "Never"}
                        </span>
                        {schedule.next_run_at && (
                          <span>
                            Next:{" "}
                            {new Date(schedule.next_run_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        onClick={() => handleToggleSchedule(schedule)}
                        className={`px-2.5 py-1 text-xs rounded-lg border font-medium transition ${
                          schedule.enabled
                            ? "bg-emerald-950/40 border-emerald-800 text-emerald-300 hover:bg-emerald-900/50"
                            : "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800"
                        }`}
                      >
                        {schedule.enabled ? "Enabled" : "Disabled"}
                      </button>

                      <button
                        onClick={() => {
                          setEditingSchedule(schedule);
                          setEditForm({
                            name: schedule.name,
                            cron_expression: schedule.cron_expression,
                            interval_seconds: schedule.interval_seconds,
                            enabled: schedule.enabled,
                          });
                        }}
                        className="p-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 text-xs transition"
                        title="Edit schedule"
                      >
                        Edit
                      </button>

                      <button
                        onClick={() => handleRunNow(schedule)}
                        disabled={isRunning}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm transition"
                      >
                        {isRunning ? (
                          <>
                            <ActivityIcon className="w-3.5 h-3.5 animate-spin" /> Running...
                          </>
                        ) : (
                          <>
                            <PlayIcon className="w-3.5 h-3.5" /> Run Now
                          </>
                        )}
                      </button>

                      <button
                        onClick={() => handleDeleteSchedule(schedule.id)}
                        className="p-1.5 bg-slate-900 hover:bg-rose-950 border border-slate-800 hover:border-rose-800 text-slate-400 hover:text-rose-300 rounded-lg transition"
                        title="Delete schedule"
                      >
                        <Trash2Icon className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}

              {schedules.length === 0 && (
                <div className="py-12 text-center text-xs text-slate-500">
                  No pipeline schedules configured. Click &quot;New Schedule&quot; to register automated jobs.
                </div>
              )}
            </div>
          </Card>

          {/* Execution History Table */}
          <Card>
            <CardHeader
              title="Recent Pipeline Execution History"
              subtitle="Audit log of automated scraper runs, extracted items, and diagnostic traces"
              icon={<CheckCircleIcon className="w-5 h-5" />}
            />

            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {executions.map((exec) => (
                <div
                  key={exec.id}
                  onClick={() => setSelectedExecution(exec)}
                  className="p-3 bg-slate-950/60 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 rounded-lg cursor-pointer transition flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <Badge
                      variant={
                        exec.status === "success"
                          ? "success"
                          : exec.status === "failed"
                          ? "danger"
                          : "info"
                      }
                      size="sm"
                    >
                      {exec.status}
                    </Badge>
                    <span className="font-semibold text-slate-200">{exec.job_type}</span>
                    <span className="text-[11px] text-slate-500 font-mono">
                      {new Date(exec.started_at).toLocaleString()}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-[11px] font-mono">
                    <span className="text-slate-400">
                      Processed: <strong className="text-slate-200">{exec.items_processed}</strong> items
                    </span>
                    <span className="text-sky-400 hover:underline">View Log</span>
                  </div>
                </div>
              ))}

              {executions.length === 0 && (
                <div className="py-8 text-center text-xs text-slate-500">
                  No execution runs recorded yet.
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right 1 Col: Live AI Scraper Test Bench */}
        <div className="space-y-4">
          <Card>
            <CardHeader
              title="Live Web Scraper & AI Test Bench"
              subtitle="Test real-time HTML/RSS fetch and AI extraction"
              icon={<SparklesIcon className="w-5 h-5 text-sky-400" />}
            />

            <form onSubmit={handleRunTestScrape} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Target Article or Hub URL</label>
                <input
                  type="url"
                  required
                  placeholder="https://www.aljazeera.com/news/middleeast/..."
                  value={testUrl}
                  onChange={(e) => setTestUrl(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono focus:outline-none focus:border-sky-500"
                />
              </div>

              <button
                type="submit"
                disabled={isScraping}
                className="w-full py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center justify-center gap-1.5"
              >
                {isScraping ? (
                  <>
                    <ActivityIcon className="w-3.5 h-3.5 animate-spin" /> Scraping & Extracting...
                  </>
                ) : (
                  <>
                    <GlobeIcon className="w-3.5 h-3.5" /> Scrape & Extract Now
                  </>
                )}
              </button>
            </form>

            {testError && (
              <div className="p-3 mt-3 bg-rose-950/30 border border-rose-800/40 rounded-lg text-xs text-rose-300 font-mono">
                {testError}
              </div>
            )}

            {testResult && (
              <div className="mt-4 p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-2 text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="font-bold text-slate-200 truncate max-w-[200px]">
                    {testResult.title || "Scraped Document"}
                  </span>
                  <Badge variant="success" size="sm">
                    Status: {testResult.status_code}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-slate-400">
                  <span>Language: <strong className="text-slate-200 uppercase">{testResult.detected_language || "N/A"}</strong></span>
                  <span>Chunks: <strong className="text-slate-200">{testResult.chunks_count}</strong></span>
                </div>

                {testResult.extracted_text && (
                  <div>
                    <span className="text-[10px] font-bold uppercase text-slate-500 block mb-1">
                      Extracted Text Preview:
                    </span>
                    <p className="p-2.5 bg-slate-900/90 rounded border border-slate-800/80 text-[11px] text-slate-300 max-h-48 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                      {testResult.extracted_text}
                    </p>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Execution Log Modal */}
      {selectedExecution && (
        <Modal
          isOpen={!!selectedExecution}
          onClose={() => setSelectedExecution(null)}
          title={`Execution Log: ${selectedExecution.job_type}`}
          subtitle={`Status: ${selectedExecution.status} • Processed: ${selectedExecution.items_processed} items`}
          maxWidth="2xl"
        >
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between font-mono text-[11px] text-slate-400 border-b border-slate-800 pb-2">
              <span>Started: {new Date(selectedExecution.started_at).toLocaleString()}</span>
              <span>
                Completed:{" "}
                {selectedExecution.completed_at
                  ? new Date(selectedExecution.completed_at).toLocaleString()
                  : "Running"}
              </span>
            </div>

            {selectedExecution.error_message && (
              <div className="p-3 bg-rose-950/40 border border-rose-800 rounded-lg text-rose-300 font-mono">
                Error: {selectedExecution.error_message}
              </div>
            )}

            <div>
              <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono mb-1">
                Diagnostic Trace Logs
              </h5>
              <pre className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 text-[11px] font-mono text-slate-300 max-h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                {selectedExecution.log_output || "No log trace recorded for this run."}
              </pre>
            </div>
          </div>
        </Modal>
      )}

      {/* Create Schedule Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create Automated Pipeline Schedule"
        subtitle="Configure an automated background job for data collection, extraction, or model evaluation"
        maxWidth="md"
      >
        <form onSubmit={handleCreateSchedule} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Schedule Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Daily Middle East News & OSINT Scraping"
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Pipeline Job Type</label>
            <select
              value={createForm.job_type}
              onChange={(e) => setCreateForm({ ...createForm, job_type: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="daily_news_scraping">Daily News & OSINT Scraping</option>
              <option value="satellite_ingestion">Satellite & Thermal Sensor Ingestion</option>
              <option value="social_broadcast_scraping">Social & Official Broadcast Ingestion</option>
              <option value="risk_recalculation">Active Conflict Risk Recalculation</option>
              <option value="scenario_evaluation">Scenario Signposts & Probabilities</option>
              <option value="forecast_evaluation">Forecast Calibration & Due Audit</option>
              <option value="daily_brief_generation">Executive Daily Intelligence Brief</option>
              <option value="monitor_evaluation">Real-Time Intelligence Monitors</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Interval (Seconds)</label>
              <input
                type="number"
                min="60"
                value={createForm.interval_seconds || 86400}
                onChange={(e) =>
                  setCreateForm({ ...createForm, interval_seconds: Number(e.target.value) })
                }
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Cron Expression</label>
              <input
                type="text"
                placeholder="0 6 * * *"
                value={createForm.cron_expression || ""}
                onChange={(e) => setCreateForm({ ...createForm, cron_expression: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsCreateOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isCreating}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition"
            >
              {isCreating ? "Saving..." : "Create Schedule"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Schedule Modal */}
      {editingSchedule && (
        <Modal
          isOpen={!!editingSchedule}
          onClose={() => setEditingSchedule(null)}
          title={`Edit Schedule: ${editingSchedule.name}`}
          subtitle={`Job Type: ${editingSchedule.job_type}`}
          maxWidth="md"
        >
          <form onSubmit={handleUpdateSchedule} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Schedule Name</label>
              <input
                type="text"
                required
                value={editForm.name || ""}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Interval (Seconds)</label>
                <input
                  type="number"
                  min="60"
                  value={editForm.interval_seconds || 86400}
                  onChange={(e) =>
                    setEditForm({ ...editForm, interval_seconds: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Cron Expression</label>
                <input
                  type="text"
                  value={editForm.cron_expression || ""}
                  onChange={(e) => setEditForm({ ...editForm, cron_expression: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="edit_enabled"
                checked={editForm.enabled ?? true}
                onChange={(e) => setEditForm({ ...editForm, enabled: e.target.checked })}
                className="rounded bg-slate-950 border-slate-800 text-sky-600 focus:ring-0"
              />
              <label htmlFor="edit_enabled" className="text-xs text-slate-200">
                Active / Enabled for background execution
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setEditingSchedule(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isUpdating}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition"
              >
                {isUpdating ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import {
  Investigation,
  InvestigationDetail,
  CreateInvestigationRequest,
} from "../../types";
import { investigationsService } from "../../services";
import {
  SearchIcon,
  PlusIcon,
  ActivityIcon,
  RefreshCwIcon,
  CheckCircleIcon,
  AlertTriangleIcon,
} from "../common/Icons";
import { Card, CardHeader } from "../common/Card";
import { Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function InvestigationsView() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [selectedInvestigation, setSelectedInvestigation] = useState<InvestigationDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [priorityFilter, setPriorityFilter] = useState<string>("");

  // Launch Investigation Modal
  const [isLaunchOpen, setIsLaunchOpen] = useState(false);
  const [launchForm, setLaunchForm] = useState<CreateInvestigationRequest>({
    title: "",
    question: "",
    priority: "medium",
  });
  const [isLaunching, setIsLaunching] = useState(false);

  const fetchInvestigations = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await investigationsService.listInvestigations({
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
      });
      setInvestigations(data);
    } catch (err) {
      console.error("Investigations fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load investigations");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInvestigations();
  }, [statusFilter, priorityFilter]);

  const handleSelectInvestigation = async (inv: Investigation) => {
    setLoadingDetail(true);
    try {
      const detail = await investigationsService.getInvestigation(inv.id);
      setSelectedInvestigation(detail);
    } catch (err) {
      console.error("Detail error:", err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!launchForm.title.trim() || !launchForm.question.trim()) return;

    setIsLaunching(true);
    try {
      const created = await investigationsService.createInvestigation(launchForm);
      setIsLaunchOpen(false);
      setLaunchForm({ title: "", question: "", priority: "medium" });
      fetchInvestigations();
      const detail = await investigationsService.getInvestigation(created.id);
      setSelectedInvestigation(detail);
    } catch (err) {
      console.error("Launch error:", err);
    } finally {
      setIsLaunching(false);
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading intelligence investigation workflows..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchInvestigations} />;
  }

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <SearchIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Intelligence Investigations Workspace
            </h2>
            <p className="text-xs text-slate-400">
              Autonomous multi-step investigation pipeline &bull; Hypothesis verification &bull; Auditable step execution
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 cursor-pointer"
          >
            <option value="" className="bg-slate-900">All Priorities</option>
            <option value="critical" className="bg-slate-900">Critical</option>
            <option value="high" className="bg-slate-900">High</option>
            <option value="medium" className="bg-slate-900">Medium</option>
            <option value="low" className="bg-slate-900">Low</option>
          </select>

          <button
            onClick={fetchInvestigations}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCwIcon className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsLaunchOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            <PlusIcon className="w-4 h-4" />
            Launch Case
          </button>
        </div>
      </div>

      {/* Grid Layout: Case List & Step Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Case Files */}
        <div className="space-y-3 max-h-[calc(100vh-16rem)] overflow-y-auto pr-1">
          {investigations.map((inv) => {
            const isSelected = selectedInvestigation?.id === inv.id;
            return (
              <div
                key={inv.id}
                onClick={() => handleSelectInvestigation(inv)}
                className={`p-4 rounded-xl border cursor-pointer transition space-y-2 ${
                  isSelected
                    ? "bg-slate-900 border-sky-500 shadow-md ring-1 ring-sky-500/20"
                    : "bg-slate-950/60 hover:bg-slate-900 border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between">
                  <Badge
                    variant={
                      inv.priority === "critical"
                        ? "critical"
                        : inv.priority === "high"
                        ? "high"
                        : "info"
                    }
                    size="sm"
                  >
                    {inv.priority}
                  </Badge>
                  <Badge variant="neutral" size="sm">
                    {inv.status}
                  </Badge>
                </div>

                <h4 className="text-xs font-bold text-slate-100 line-clamp-2">{inv.title}</h4>

                <p className="text-[11px] text-slate-400 line-clamp-2">{inv.question}</p>

                <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1">
                  <span>Req: {inv.requested_by.slice(0, 8)}</span>
                  <span>{new Date(inv.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            );
          })}

          {investigations.length === 0 && (
            <div className="py-12 text-center text-xs text-slate-500">
              No investigations active. Click &quot;Launch Case&quot; to initiate a targeted investigation workflow.
            </div>
          )}
        </div>

        {/* Right 2 Cols: Investigation Detail & Steps Timeline */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="h-full flex flex-col justify-between">
            {loadingDetail ? (
              <LoadingState message="Inspecting investigation steps & findings..." />
            ) : selectedInvestigation ? (
              <div className="space-y-6">
                {/* Case Header */}
                <div className="border-b border-slate-800 pb-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="info">CASE #{selectedInvestigation.id.slice(0, 8)}</Badge>
                    <Badge variant="neutral">{selectedInvestigation.status}</Badge>
                    <Badge
                      variant={
                        selectedInvestigation.priority === "critical"
                          ? "critical"
                          : selectedInvestigation.priority === "high"
                          ? "high"
                          : "info"
                      }
                    >
                      {selectedInvestigation.priority} priority
                    </Badge>
                  </div>
                  <h3 className="text-base font-bold text-slate-100">
                    {selectedInvestigation.title}
                  </h3>
                  <p className="text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <strong>Investigation Question:</strong> {selectedInvestigation.question}
                  </p>
                </div>

                {/* Result Summary */}
                {selectedInvestigation.result_summary && (
                  <div className="p-4 bg-emerald-950/20 border border-emerald-800/40 rounded-xl space-y-1">
                    <h5 className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 font-mono">
                      Analytical Findings & Result Summary
                    </h5>
                    <p className="text-xs text-slate-200 leading-relaxed">
                      {selectedInvestigation.result_summary}
                    </p>
                  </div>
                )}

                {/* Steps Execution Timeline */}
                <div>
                  <h5 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono mb-3">
                    Automated Investigation Pipeline Execution ({selectedInvestigation.steps.length} Steps)
                  </h5>

                  <div className="space-y-3">
                    {selectedInvestigation.steps.map((step) => (
                      <div
                        key={step.id}
                        className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center font-mono font-bold text-[10px] text-sky-400">
                              {step.sequence}
                            </span>
                            <span className="font-semibold text-slate-200 capitalize">
                              {step.step_type.replace("_", " ")}
                            </span>
                          </div>
                          <Badge
                            variant={
                              step.status === "completed"
                                ? "success"
                                : step.status === "failed"
                                ? "danger"
                                : "info"
                            }
                            size="sm"
                          >
                            {step.status}
                          </Badge>
                        </div>

                        {/* Step Output Json details */}
                        {step.output_json && Object.keys(step.output_json).length > 0 && (
                          <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-300 max-h-32 overflow-y-auto">
                            <pre>{JSON.stringify(step.output_json, null, 2)}</pre>
                          </div>
                        )}

                        {step.error_message && (
                          <div className="text-xs text-rose-400 bg-rose-950/40 p-2 rounded border border-rose-900">
                            {step.error_message}
                          </div>
                        )}
                      </div>
                    ))}

                    {selectedInvestigation.steps.length === 0 && (
                      <div className="py-6 text-center text-xs text-slate-500">
                        Workflow queued. Steps will execute asynchronously in background.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-24 text-center text-slate-500 text-xs flex flex-col items-center justify-center">
                <SearchIcon className="w-8 h-8 text-slate-600 mb-2" />
                Select an investigation case from the left panel to inspect step breakdown.
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Launch Investigation Modal */}
      <Modal
        isOpen={isLaunchOpen}
        onClose={() => setIsLaunchOpen(false)}
        title="Launch Autonomous Investigation"
        subtitle="Deploys targeted verification queries and document collection against specific hypotheses"
        maxWidth="md"
      >
        <form onSubmit={handleLaunch} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Case Title</label>
            <input
              type="text"
              required
              placeholder="e.g. Investigation into Bab el-Mandeb Anti-Ship Munitions Origin"
              value={launchForm.title}
              onChange={(e) => setLaunchForm({ ...launchForm, title: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Core Analytical Question
            </label>
            <textarea
              rows={3}
              required
              placeholder="e.g. Identify weapon serial numbers, supplier state actor, and launch coordination patterns based on open-source imagery and maritime logs..."
              value={launchForm.question}
              onChange={(e) => setLaunchForm({ ...launchForm, question: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500 leading-relaxed"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Priority</label>
            <select
              value={launchForm.priority}
              onChange={(e) => setLaunchForm({ ...launchForm, priority: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="low">Low Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="high">High Escalation Priority</option>
              <option value="critical">Critical War Warning Priority</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsLaunchOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLaunching}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition flex items-center gap-1.5"
            >
              {isLaunching ? (
                <>
                  <ActivityIcon className="w-3.5 h-3.5 animate-spin" /> Launching...
                </>
              ) : (
                "Launch Investigation"
              )}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

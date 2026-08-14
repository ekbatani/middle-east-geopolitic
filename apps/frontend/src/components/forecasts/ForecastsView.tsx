"use client";

import React, { useState, useEffect } from "react";
import {
  Forecast,
  CalibrationReport,
  IssueForecastRequest,
  ResolveForecastRequest,
  ForecastOutcome,
} from "../../types";
import { forecastsService } from "../../services";
import {
  TargetIcon,
  PlusIcon,
  ActivityIcon,
  RefreshCwIcon,
  CheckCircleIcon,
  BarChart3Icon,
} from "../common/Icons";
import { Card, CardHeader } from "../common/Card";
import { Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function ForecastsView() {
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [calibration, setCalibration] = useState<CalibrationReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Issue Forecast Modal
  const [isIssueOpen, setIsIssueOpen] = useState(false);
  const [issueForm, setIssueForm] = useState<IssueForecastRequest>({
    question: "",
    resolution_date: new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10),
    probability: 65,
    confidence: 0.8,
    assumptions: [""],
  });
  const [isIssuing, setIsIssuing] = useState(false);

  // Resolve Forecast Modal
  const [resolvingForecast, setResolvingForecast] = useState<Forecast | null>(null);
  const [resolveOutcome, setResolveOutcome] = useState<ForecastOutcome>("occurred");
  const [evaluationNote, setEvaluationNote] = useState("");
  const [isResolving, setIsResolving] = useState(false);

  const fetchForecastsData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [fData, calData] = await Promise.all([
        forecastsService.listForecasts(),
        forecastsService.getCalibration(),
      ]);
      setForecasts(fData);
      setCalibration(calData);
    } catch (err) {
      console.error("Forecasts fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load forecasts");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchForecastsData();
  }, []);

  const handleIssueForecast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!issueForm.question.trim()) return;

    setIsIssuing(true);
    try {
      await forecastsService.issueForecast({
        ...issueForm,
        assumptions: issueForm.assumptions?.filter((a) => a.trim().length > 0) || [],
      });
      setIsIssueOpen(false);
      setIssueForm({
        question: "",
        resolution_date: new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10),
        probability: 65,
        confidence: 0.8,
        assumptions: [""],
      });
      fetchForecastsData();
    } catch (err) {
      console.error("Issue forecast error:", err);
    } finally {
      setIsIssuing(false);
    }
  };

  const handleResolveForecast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingForecast) return;

    setIsResolving(true);
    try {
      await forecastsService.resolveForecast(resolvingForecast.id, {
        outcome: resolveOutcome,
        evaluation_note: evaluationNote.trim() || undefined,
      });
      setResolvingForecast(null);
      setEvaluationNote("");
      fetchForecastsData();
    } catch (err) {
      console.error("Resolve forecast error:", err);
    } finally {
      setIsResolving(false);
    }
  };

  if (isLoading) {
    return <LoadingState message="Calculating Brier reliability scores and forecast calibration..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchForecastsData} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <TargetIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Probabilistic Forecasts & Brier Calibration Dashboard
            </h2>
            <p className="text-xs text-slate-400">
              Quantitative prediction auditing &bull; Strict Brier scoring &bull; Calibration curve evaluation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchForecastsData}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCwIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsIssueOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            <PlusIcon className="w-4 h-4" />
            Issue Prediction
          </button>
        </div>
      </div>

      {/* Calibration Summary Stats Card */}
      {calibration && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="p-4 bg-slate-950 border border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-400">
              Overall Brier Score (0.0 = Perfect)
            </span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold font-mono text-sky-400">
                {calibration.overall_brier_score !== null && calibration.overall_brier_score !== undefined
                  ? calibration.overall_brier_score.toFixed(3)
                  : "N/A"}
              </span>
              <span className="text-xs text-slate-500">Mean Squared Error</span>
            </div>
          </Card>

          <Card className="p-4 bg-slate-950 border border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-400">Resolved Forecasts</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold font-mono text-emerald-400">
                {calibration.resolved_count}
              </span>
              <span className="text-xs text-slate-500">Audited outcomes</span>
            </div>
          </Card>

          <Card className="p-4 bg-slate-950 border border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-400">Active Open Predictions</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold font-mono text-amber-400">
                {calibration.open_count}
              </span>
              <span className="text-xs text-slate-500">Awaiting resolution date</span>
            </div>
          </Card>
        </div>
      )}

      {/* Forecasts Table / List */}
      <Card>
        <CardHeader
          title="Active & Historical Geopolitical Forecasts"
          subtitle={`${forecasts.length} total predictions in audit register`}
          icon={<TargetIcon className="w-5 h-5" />}
        />

        <div className="space-y-3">
          {forecasts.map((f) => {
            const isResolved = f.status === "resolved";
            return (
              <div
                key={f.id}
                className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-2.5 transition hover:border-slate-700"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-lg font-black font-mono px-2 py-0.5 rounded ${
                        f.probability >= 70
                          ? "bg-rose-950 text-rose-300 border border-rose-800"
                          : f.probability >= 40
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : "bg-sky-950 text-sky-300 border border-sky-800"
                      }`}
                    >
                      {f.probability}%
                    </span>
                    <Badge variant={isResolved ? "neutral" : "info"} size="sm">
                      {f.status}
                    </Badge>
                    {f.outcome && (
                      <Badge
                        variant={
                          f.outcome === "occurred"
                            ? "success"
                            : f.outcome === "did_not_occur"
                            ? "danger"
                            : "warning"
                        }
                        size="sm"
                      >
                        Outcome: {f.outcome.replace("_", " ")}
                      </Badge>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                    <span>Target: {f.resolution_date}</span>
                    {f.brier_score !== null && f.brier_score !== undefined && (
                      <span className="text-sky-300 font-bold">
                        Brier: {f.brier_score.toFixed(3)}
                      </span>
                    )}
                  </div>
                </div>

                <h4 className="text-sm font-semibold text-slate-100">{f.question}</h4>

                {/* Assumptions */}
                {f.assumptions.length > 0 && (
                  <div className="text-xs text-slate-400 bg-slate-900/60 p-2 rounded-lg border border-slate-800/60">
                    <span className="font-mono text-[10px] text-slate-500 uppercase font-bold block mb-1">
                      Key Analytical Assumptions:
                    </span>
                    <ul className="list-disc list-inside space-y-0.5">
                      {f.assumptions.map((a, i) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Resolve Action */}
                {!isResolved && (
                  <div className="flex justify-end pt-1">
                    <button
                      onClick={() => {
                        setResolvingForecast(f);
                        setResolveOutcome("occurred");
                        setEvaluationNote("");
                      }}
                      className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
                    >
                      Resolve & Audit Brier Score
                    </button>
                  </div>
                )}
              </div>
            );
          })}

          {forecasts.length === 0 && (
            <div className="py-12 text-center text-xs text-slate-500">
              No forecasts in audit register. Click &quot;Issue Prediction&quot; to issue the first probabilistic prediction.
            </div>
          )}
        </div>
      </Card>

      {/* Issue Forecast Modal */}
      <Modal
        isOpen={isIssueOpen}
        onClose={() => setIsIssueOpen(false)}
        title="Issue Probabilistic Geopolitical Forecast"
        subtitle="Formal prediction with specified resolution deadline and auditable assumptions"
        maxWidth="lg"
      >
        <form onSubmit={handleIssueForecast} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Falsifiable Target Question
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Will Israel conduct kinetic strikes against Iranian nuclear enrichment sites before October 2026?"
              value={issueForm.question}
              onChange={(e) => setIssueForm({ ...issueForm, question: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Resolution Date
              </label>
              <input
                type="date"
                required
                value={issueForm.resolution_date}
                onChange={(e) => setIssueForm({ ...issueForm, resolution_date: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Probability ({issueForm.probability}%)
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={issueForm.probability}
                onChange={(e) => setIssueForm({ ...issueForm, probability: Number(e.target.value) })}
                className="w-full mt-2"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Confidence (0.0–1.0)
              </label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={issueForm.confidence}
                onChange={(e) => setIssueForm({ ...issueForm, confidence: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Core Assumptions
            </label>
            {issueForm.assumptions?.map((assump, idx) => (
              <div key={idx} className="flex items-center gap-2 mb-2">
                <input
                  type="text"
                  placeholder={`Assumption #${idx + 1}`}
                  value={assump}
                  onChange={(e) => {
                    const next = [...(issueForm.assumptions || [])];
                    next[idx] = e.target.value;
                    setIssueForm({ ...issueForm, assumptions: next });
                  }}
                  className="flex-1 px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100"
                />
              </div>
            ))}
            <button
              type="button"
              onClick={() =>
                setIssueForm({
                  ...issueForm,
                  assumptions: [...(issueForm.assumptions || []), ""],
                })
              }
              className="text-xs text-sky-400 hover:text-sky-300 font-medium"
            >
              + Add Assumption
            </button>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsIssueOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isIssuing}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition"
            >
              {isIssuing ? "Issuing..." : "Issue Forecast"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Resolve Forecast Modal */}
      {resolvingForecast && (
        <Modal
          isOpen={!!resolvingForecast}
          onClose={() => setResolvingForecast(null)}
          title="Resolve Geopolitical Forecast"
          subtitle={resolvingForecast.question}
          maxWidth="md"
        >
          <form onSubmit={handleResolveForecast} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Final Outcome</label>
              <select
                value={resolveOutcome}
                onChange={(e) => setResolveOutcome(e.target.value as ForecastOutcome)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="occurred">Occurred (Target Event Happened)</option>
                <option value="did_not_occur">Did Not Occur (Event Did Not Happen)</option>
                <option value="ambiguous">Ambiguous / Inconclusive</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Post-Mortem & Evaluation Note
              </label>
              <textarea
                rows={3}
                placeholder="Details on verification evidence, date of occurrence, or why outcome was determined..."
                value={evaluationNote}
                onChange={(e) => setEvaluationNote(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setResolvingForecast(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isResolving}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition"
              >
                {isResolving ? "Computing Brier..." : "Confirm Resolution"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

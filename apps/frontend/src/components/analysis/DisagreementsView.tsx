"use client";

import React, { useState, useEffect } from "react";
import {
  ModelReviewResult,
  DisagreementSummary,
  RecordPositionRequest,
  DisagreementSubjectType,
} from "../../types";
import { modelReviewsService, analystService } from "../../services";
import {
  BotIcon,
  UsersIcon,
  PlusIcon,
  RefreshCwIcon,
  ActivityIcon,
  CheckCircleIcon,
  AlertTriangleIcon,
} from "../common/Icons";
import { Card, CardHeader } from "../common/Card";
import { Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function DisagreementsView() {
  const [modelReviews, setModelReviews] = useState<ModelReviewResult[]>([]);
  const [disagreements, setDisagreements] = useState<DisagreementSummary[]>([]);
  const [activeTab, setActiveTab] = useState<"model_reviews" | "analyst_disagreements">(
    "model_reviews"
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Record Position Modal
  const [isRecordOpen, setIsRecordOpen] = useState(false);
  const [recordForm, setRecordForm] = useState<RecordPositionRequest>({
    subject_type: "claim",
    subject_id: "",
    stance: "supports",
    score: 75,
    confidence: 0.85,
    rationale: "",
  });
  const [isRecording, setIsRecording] = useState(false);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [mrData, dData] = await Promise.all([
        modelReviewsService.listModelReviews({ limit: 50 }),
        analystService.listDisagreements({ limit: 50 }),
      ]);
      setModelReviews(mrData);
      setDisagreements(dData);
    } catch (err) {
      console.error("Disagreements fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load disagreements data");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRecordPosition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!recordForm.subject_id.trim()) return;

    setIsRecording(true);
    try {
      await analystService.recordPosition(recordForm);
      setIsRecordOpen(false);
      setRecordForm({
        subject_type: "claim",
        subject_id: "",
        stance: "supports",
        score: 75,
        confidence: 0.85,
        rationale: "",
      });
      fetchData();
    } catch (err) {
      console.error("Record position error:", err);
    } finally {
      setIsRecording(false);
    }
  };

  if (isLoading && modelReviews.length === 0 && disagreements.length === 0) {
    return <LoadingState message="Cross-verifying multi-model LLM stances and analyst consensus..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-6">
      {/* Header & Mode Tabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <BotIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Multi-Model AI Reviews & Analyst Stance Disagreements
            </h2>
            <p className="text-xs text-slate-400">
              Comparative multi-LLM validation &bull; High-impact score deltas &bull; Human analyst disagreement tracking
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
            onClick={() => setIsRecordOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            <PlusIcon className="w-4 h-4" />
            Record Analyst Position
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("model_reviews")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
            activeTab === "model_reviews"
              ? "bg-sky-600 text-white shadow-sm"
              : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
          }`}
        >
          <BotIcon className="w-4 h-4" />
          Multi-Model LLM Reviews ({modelReviews.length})
        </button>

        <button
          onClick={() => setActiveTab("analyst_disagreements")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
            activeTab === "analyst_disagreements"
              ? "bg-sky-600 text-white shadow-sm"
              : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
          }`}
        >
          <UsersIcon className="w-4 h-4" />
          Analyst Stance Disagreements ({disagreements.length})
        </button>
      </div>

      {/* Tab 1: Multi-Model LLM Reviews */}
      {activeTab === "model_reviews" && (
        <div className="space-y-4">
          {modelReviews.map((rev) => {
            const hasAgreement = rev.agreement;
            const delta = rev.agreement_delta ?? Math.abs(rev.primary_final_score - rev.secondary_final_score);

            return (
              <Card
                key={rev.id}
                className="p-5 bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={hasAgreement ? "success" : "danger"}>
                      {hasAgreement ? "Models Agree" : "Score Disagreement"}
                    </Badge>
                    <Badge variant="neutral">{rev.subject_type.replace("_", " ")}</Badge>
                    <span className="text-xs text-slate-400 font-mono">
                      Delta: &plusmn;{delta} pts
                    </span>
                  </div>

                  <span className="text-[11px] font-mono text-slate-500">
                    Reviewed: {new Date(rev.reviewed_at).toLocaleString()}
                  </span>
                </div>

                <div className="text-xs text-slate-300">
                  <span className="text-slate-500 font-mono">Trigger Reason:</span> {rev.trigger_reason}
                </div>

                {/* Comparative Models Scores */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-3.5 bg-slate-900 rounded-xl border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-sky-400">
                        Primary Model ({rev.primary_model})
                      </span>
                      <span className="text-xl font-bold font-mono text-slate-100">
                        {rev.primary_final_score}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Baseline production risk engine score
                    </span>
                  </div>

                  <div className="p-3.5 bg-slate-900 rounded-xl border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-amber-400">
                        Secondary Model ({rev.secondary_model})
                      </span>
                      <span className="text-xl font-bold font-mono text-slate-100">
                        {rev.secondary_final_score}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Independent secondary cross-evaluation
                    </span>
                  </div>
                </div>

                {/* Secondary Model reasoning payload */}
                {rev.secondary_output_json && Object.keys(rev.secondary_output_json).length > 0 && (
                  <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800/80 text-[11px] font-mono text-slate-300 max-h-36 overflow-y-auto">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                      Secondary Model Output JSON:
                    </span>
                    <pre>{JSON.stringify(rev.secondary_output_json, null, 2)}</pre>
                  </div>
                )}
              </Card>
            );
          })}

          {modelReviews.length === 0 && (
            <div className="py-16 text-center text-xs text-slate-500 bg-slate-950 rounded-2xl border border-slate-800">
              No multi-model reviews recorded yet. High-impact risk assessments trigger automated secondary model reviews.
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Analyst Disagreements */}
      {activeTab === "analyst_disagreements" && (
        <div className="space-y-4">
          {disagreements.map((dis, i) => (
            <Card
              key={i}
              className="p-5 bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Badge variant="warning">Spread &gt;= {dis.score_spread ?? "N/A"}</Badge>
                  <Badge variant="info">{dis.subject_type}</Badge>
                </div>
                <span className="text-[11px] font-mono text-slate-500">
                  Subject ID: {dis.subject_id}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 pt-2">
                <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-center">
                  <span className="text-[10px] uppercase font-mono text-slate-500 block">Positions</span>
                  <span className="text-lg font-bold text-slate-100 font-mono">
                    {dis.position_count}
                  </span>
                </div>

                <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-center">
                  <span className="text-[10px] uppercase font-mono text-slate-500 block">Distinct Stances</span>
                  <span className="text-lg font-bold text-amber-400 font-mono">
                    {dis.distinct_stances}
                  </span>
                </div>

                <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-center">
                  <span className="text-[10px] uppercase font-mono text-slate-500 block">Score Spread</span>
                  <span className="text-lg font-bold text-rose-400 font-mono">
                    {dis.score_spread !== null && dis.score_spread !== undefined
                      ? `${dis.score_spread} pts`
                      : "—"}
                  </span>
                </div>
              </div>
            </Card>
          ))}

          {disagreements.length === 0 && (
            <div className="py-16 text-center text-xs text-slate-500 bg-slate-950 rounded-2xl border border-slate-800">
              No significant analyst disagreements detected across current positions.
            </div>
          )}
        </div>
      )}

      {/* Record Position Modal */}
      <Modal
        isOpen={isRecordOpen}
        onClose={() => setIsRecordOpen(false)}
        title="Record Independent Analyst Position"
        subtitle="Log your individual probability or stance on a specific intelligence subject"
        maxWidth="md"
      >
        <form onSubmit={handleRecordPosition} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Subject Type</label>
              <select
                value={recordForm.subject_type}
                onChange={(e) =>
                  setRecordForm({
                    ...recordForm,
                    subject_type: e.target.value as DisagreementSubjectType,
                  })
                }
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="claim">Claim</option>
                <option value="event">Event</option>
                <option value="risk_assessment">Risk Assessment</option>
                <option value="scenario">Scenario</option>
                <option value="relationship">Relationship</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Subject UUID</label>
              <input
                type="text"
                required
                placeholder="UUID..."
                value={recordForm.subject_id}
                onChange={(e) => setRecordForm({ ...recordForm, subject_id: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Stance</label>
              <select
                value={recordForm.stance || "supports"}
                onChange={(e) => setRecordForm({ ...recordForm, stance: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="supports">Supports</option>
                <option value="refutes">Refutes</option>
                <option value="neutral">Neutral</option>
                <option value="escalation">Escalation</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Score (0–100)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={recordForm.score ?? 75}
                onChange={(e) => setRecordForm({ ...recordForm, score: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Confidence</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={recordForm.confidence ?? 0.85}
                onChange={(e) =>
                  setRecordForm({ ...recordForm, confidence: Number(e.target.value) })
                }
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Rationale</label>
            <textarea
              rows={3}
              placeholder="Explain analytical reasoning and primary indicators referenced..."
              value={recordForm.rationale || ""}
              onChange={(e) => setRecordForm({ ...recordForm, rationale: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500 leading-relaxed"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsRecordOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isRecording}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition"
            >
              {isRecording ? "Saving..." : "Record Position"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

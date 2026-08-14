"use client";

import React, { useState, useEffect } from "react";
import {
  RiskCatalogItem,
  RiskExplanation,
  ScopeType,
  Actor,
} from "../../types";
import { risksService, intelligenceService, actorsService } from "../../services";
import {
  ActivityIcon,
  RefreshCwIcon,
  ShieldIcon,
  SparklesIcon,
  CheckCircleIcon,
  AlertTriangleIcon,
} from "../common/Icons";
import { Card, CardHeader } from "../common/Card";
import { Badge, TrendBadge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function RiskEngineView() {
  const [risks, setRisks] = useState<RiskCatalogItem[]>([]);
  const [countries, setCountries] = useState<Actor[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected Scope Filter
  const [selectedScopeType, setSelectedScopeType] = useState<ScopeType | undefined>(undefined);
  const [selectedCountryId, setSelectedCountryId] = useState<string>("");

  // Risk Explanation Drill-down Modal
  const [explanation, setExplanation] = useState<RiskExplanation | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);

  // Recalculate Modal
  const [isRecalculateOpen, setIsRecalculateOpen] = useState(false);
  const [recalcRiskId, setRecalcRiskId] = useState<string>("");
  const [recalcScopeType, setRecalcScopeType] = useState<ScopeType>("country");
  const [recalcScopeId, setRecalcScopeId] = useState<string>("");
  const [isRecalculating, setIsRecalculating] = useState(false);

  const fetchRisks = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [risksData, actorsData] = await Promise.all([
        risksService.listRisks({
          scope_type: selectedScopeType,
          scope_id: selectedCountryId || undefined,
        }),
        actorsService.listActors({ actor_type: "country", limit: 30 }),
      ]);
      setRisks(risksData);
      setCountries(actorsData);
      if (risksData.length > 0 && !recalcRiskId) {
        setRecalcRiskId(risksData[0].definition.id);
      }
      if (actorsData.length > 0 && !recalcScopeId) {
        setRecalcScopeId(actorsData[0].id);
      }
    } catch (err) {
      console.error("Risks fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load risk catalog");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRisks();
  }, [selectedScopeType, selectedCountryId]);

  const handleExplainRisk = async (item: RiskCatalogItem) => {
    setLoadingExplanation(true);
    try {
      const expl = await intelligenceService.getRiskExplanation({
        risk_definition_id: item.definition.id,
        scope_type: selectedScopeType || "country",
        scope_id: selectedCountryId || (countries.length > 0 ? countries[0].id : null),
      });
      setExplanation(expl);
    } catch (err) {
      console.error("Explain error:", err);
    } finally {
      setLoadingExplanation(false);
    }
  };

  const handleRecalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!recalcRiskId) return;

    setIsRecalculating(true);
    try {
      await risksService.recalculateRisk({
        risk_definition_id: recalcRiskId,
        scope_type: recalcScopeType,
        scope_id: recalcScopeType === "country" ? recalcScopeId || undefined : undefined,
      });
      setIsRecalculateOpen(false);
      fetchRisks();
    } catch (err) {
      console.error("Recalculate error:", err);
    } finally {
      setIsRecalculating(false);
    }
  };

  if (isLoading) {
    return <LoadingState message="Calibrating multi-indicator risk engine scoring models..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchRisks} />;
  }

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-amber-400">
            <ActivityIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Deterministic Risk Engine & Indicator Decomposition
            </h2>
            <p className="text-xs text-slate-400">
              Weighted indicator scoring &bull; Bounded LLM adjustments [-10, +10] &bull; Auditable evidence trails
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Scope type filter */}
          <select
            value={selectedScopeType || ""}
            onChange={(e) =>
              setSelectedScopeType(e.target.value ? (e.target.value as ScopeType) : undefined)
            }
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 cursor-pointer"
          >
            <option value="" className="bg-slate-900">All Scope Types</option>
            <option value="country" className="bg-slate-900">Country Level</option>
            <option value="regional" className="bg-slate-900">Regional / Middle East</option>
            <option value="global" className="bg-slate-900">Global Systemic</option>
          </select>

          {/* Country selector if country scope */}
          {selectedScopeType === "country" && (
            <select
              value={selectedCountryId}
              onChange={(e) => setSelectedCountryId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 cursor-pointer"
            >
              <option value="" className="bg-slate-900">All Countries</option>
              {countries.map((c) => (
                <option key={c.id} value={c.id} className="bg-slate-900">
                  {c.canonical_name}
                </option>
              ))}
            </select>
          )}

          <button
            onClick={() => setIsRecalculateOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs rounded-lg shadow-sm transition"
          >
            <SparklesIcon className="w-3.5 h-3.5" />
            Recalculate Risk
          </button>
        </div>
      </div>

      {/* Risk Definitions & Assessments Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {risks.map((item) => {
          const assessment = item.latest_assessment;
          const score = assessment?.final_score ?? 0;
          const isHigh = score >= 65;
          const isElevated = score >= 45 && score < 65;

          return (
            <Card
              key={item.definition.id}
              className="flex flex-col justify-between hover:border-slate-700 transition space-y-4"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                      {item.definition.code}
                    </span>
                    <h3 className="text-sm font-bold text-slate-100">{item.definition.name}</h3>
                  </div>

                  <div className="text-right">
                    <div className="text-2xl font-black font-mono">
                      <span
                        className={
                          isHigh
                            ? "text-rose-400"
                            : isElevated
                            ? "text-amber-400"
                            : "text-emerald-400"
                        }
                      >
                        {score}
                      </span>
                      <span className="text-xs text-slate-500 font-normal">/100</span>
                    </div>
                  </div>
                </div>

                <p className="text-xs text-slate-400 line-clamp-2 mb-3">
                  {item.definition.description || "Systemic geopolitical risk category."}
                </p>

                {assessment && (
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">Deterministic Base:</span>
                      <span className="font-mono text-slate-200">{assessment.base_score}</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">LLM Adjustment:</span>
                      <span
                        className={`font-mono ${
                          assessment.llm_adjustment > 0
                            ? "text-rose-400 font-semibold"
                            : assessment.llm_adjustment < 0
                            ? "text-emerald-400 font-semibold"
                            : "text-slate-400"
                        }`}
                      >
                        {assessment.llm_adjustment > 0 ? `+${assessment.llm_adjustment}` : assessment.llm_adjustment}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">Assessment Trend:</span>
                      <TrendBadge trend={assessment.trend} />
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-[10px] text-slate-400 font-mono">
                  RULESET: {item.definition.ruleset_version}
                </span>

                <button
                  onClick={() => handleExplainRisk(item)}
                  className="text-xs text-sky-400 hover:text-sky-300 font-medium flex items-center gap-1"
                >
                  Indicator Breakdown &rarr;
                </button>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Risk Explanation Modal */}
      {explanation && (
        <Modal
          isOpen={!!explanation}
          onClose={() => setExplanation(null)}
          title={`Risk Decomposition: ${explanation.risk_name}`}
          subtitle={`Score: ${explanation.final_score}/100 • Trend: ${explanation.trend.toUpperCase()} • Ruleset: ${explanation.ruleset_version}`}
          maxWidth="4xl"
        >
          <div className="space-y-5">
            {/* Narrative Explanation */}
            {explanation.explanation && (
              <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-200 leading-relaxed">
                <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono mb-1">
                  Engine Assessment Summary
                </h5>
                <p>{explanation.explanation}</p>
              </div>
            )}

            {/* Changed / Counter Indicators */}
            {(explanation.changed_indicators.length > 0 ||
              explanation.counter_indicators.length > 0) && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {explanation.changed_indicators.length > 0 && (
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                    <h5 className="text-[10px] font-bold uppercase tracking-wider text-amber-400 font-mono mb-1.5">
                      Changed Indicators Diff
                    </h5>
                    <div className="flex flex-wrap gap-1">
                      {explanation.changed_indicators.map((ind) => (
                        <Badge key={ind} variant="warning" size="sm">
                          {ind}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {explanation.counter_indicators.length > 0 && (
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                    <h5 className="text-[10px] font-bold uppercase tracking-wider text-sky-400 font-mono mb-1.5">
                      Counter-Indicators & Dampeners
                    </h5>
                    <div className="flex flex-wrap gap-1">
                      {explanation.counter_indicators.map((ind) => (
                        <Badge key={ind} variant="info" size="sm">
                          {ind}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Contributing Indicators Table */}
            <div>
              <h5 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono mb-2">
                Sub-Indicator Weights & Observed Values
              </h5>
              <div className="overflow-x-auto border border-slate-800 rounded-xl bg-slate-950">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/80 text-[10px] uppercase font-mono text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-3 py-2.5">Indicator</th>
                      <th className="px-3 py-2.5">Weight</th>
                      <th className="px-3 py-2.5">Direction</th>
                      <th className="px-3 py-2.5">Raw Value</th>
                      <th className="px-3 py-2.5">Normalized</th>
                      <th className="px-3 py-2.5">Contribution</th>
                      <th className="px-3 py-2.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    {explanation.contributions.map((c) => (
                      <tr key={c.indicator_code} className="hover:bg-slate-900/50">
                        <td className="px-3 py-2 font-sans font-semibold text-slate-200">
                          {c.indicator_name}{" "}
                          <span className="text-[10px] text-slate-500">({c.indicator_code})</span>
                        </td>
                        <td className="px-3 py-2 text-slate-300">{c.weight.toFixed(2)}</td>
                        <td className="px-3 py-2 capitalize text-slate-400">{c.direction}</td>
                        <td className="px-3 py-2 text-slate-200">
                          {c.raw_value !== null && c.raw_value !== undefined
                            ? c.raw_value.toFixed(1)
                            : "—"}
                        </td>
                        <td className="px-3 py-2 text-sky-400">
                          {c.normalized_value !== null && c.normalized_value !== undefined
                            ? `${Math.round(c.normalized_value * 100)}%`
                            : "—"}
                        </td>
                        <td className="px-3 py-2 font-bold text-amber-400">
                          {c.contribution !== null && c.contribution !== undefined
                            ? c.contribution.toFixed(1)
                            : "—"}
                        </td>
                        <td className="px-3 py-2">
                          {c.stale ? (
                            <Badge variant="warning" size="sm">
                              Stale
                            </Badge>
                          ) : c.included ? (
                            <Badge variant="success" size="sm">
                              Active
                            </Badge>
                          ) : (
                            <Badge variant="neutral" size="sm">
                              Excluded
                            </Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Recalculate Modal */}
      <Modal
        isOpen={isRecalculateOpen}
        onClose={() => setIsRecalculateOpen(false)}
        title="Trigger Risk Engine Recalculation"
        subtitle="Executes the deterministic scoring pipeline with bounded LLM contextual adjustment"
        maxWidth="md"
      >
        <form onSubmit={handleRecalculate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Target Risk Definition
            </label>
            <select
              value={recalcRiskId}
              onChange={(e) => setRecalcRiskId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            >
              {risks.map((r) => (
                <option key={r.definition.id} value={r.definition.id} className="bg-slate-900">
                  {r.definition.name} ({r.definition.code})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Scope Type</label>
              <select
                value={recalcScopeType}
                onChange={(e) => setRecalcScopeType(e.target.value as ScopeType)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="country">Country</option>
                <option value="regional">Regional</option>
                <option value="global">Global</option>
              </select>
            </div>

            {recalcScopeType === "country" && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Country</label>
                <select
                  value={recalcScopeId}
                  onChange={(e) => setRecalcScopeId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  {countries.map((c) => (
                    <option key={c.id} value={c.id} className="bg-slate-900">
                      {c.canonical_name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed bg-slate-950 p-3 rounded-lg border border-slate-800">
            The engine reads the latest indicator observations, computes weighted normalizations, and creates an auditable risk assessment bundle in Postgres.
          </p>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsRecalculateOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isRecalculating}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs rounded-lg transition flex items-center gap-1.5"
            >
              {isRecalculating ? (
                <>
                  <ActivityIcon className="w-3.5 h-3.5 animate-spin" /> Calculating...
                </>
              ) : (
                "Run Recalculation"
              )}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

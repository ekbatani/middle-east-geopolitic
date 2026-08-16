"use client";

import React, { useState, useEffect } from "react";
import {
  Scenario,
  ScenarioFamily,
  ScenarioStatus,
  ScenarioUpdateRecommendation,
  CreateScenarioRequest,
  UpdateScenarioRequest,
  ScenarioSimulationRequest,
  ScopeType,
} from "../../types";
import { scenariosService } from "../../services";
import {
  GlobeIcon,
  SparklesIcon,
  PlusIcon,
  ActivityIcon,
  Trash2Icon,
} from "../common/Icons";
import { Card } from "../common/Card";
import { Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function ScenariosView() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Simulation Sandbox State
  const [isSimOpen, setIsSimOpen] = useState(false);
  const [simForm, setSimForm] = useState<ScenarioSimulationRequest>({
    scope_type: "regional",
    scenario_family: "rapid_escalation",
    time_horizon: "30_days",
    hypothetical_context: "",
  });
  const [simResult, setSimResult] = useState<ScenarioUpdateRecommendation | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // Create Scenario State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState<CreateScenarioRequest>({
    name: "",
    scope_type: "regional",
    scenario_family: "status_quo",
    time_horizon: "90_days",
    description: "",
  });
  const [isCreating, setIsCreating] = useState(false);

  // Edit Scenario State
  const [editingScenario, setEditingScenario] = useState<Scenario | null>(null);
  const [editForm, setEditForm] = useState<UpdateScenarioRequest>({});
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchScenarios = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await scenariosService.listScenarios();
      setScenarios(data);
    } catch (err) {
      console.error("Scenarios fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load scenarios");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, []);

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!simForm.hypothetical_context.trim()) return;

    setIsSimulating(true);
    setSimResult(null);
    try {
      const res = await scenariosService.simulateScenario(simForm);
      setSimResult(res);
    } catch (err) {
      console.error("Simulation error:", err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleCreateScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.name.trim()) return;

    setIsCreating(true);
    try {
      await scenariosService.createScenario(createForm);
      setIsCreateOpen(false);
      setCreateForm({
        name: "",
        scope_type: "regional",
        scenario_family: "status_quo",
        time_horizon: "90_days",
        description: "",
      });
      fetchScenarios();
    } catch (err) {
      console.error("Create scenario error:", err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingScenario) return;

    setIsUpdating(true);
    try {
      await scenariosService.updateScenarioDetails(editingScenario.id, editForm);
      setEditingScenario(null);
      fetchScenarios();
    } catch (err) {
      console.error("Update scenario error:", err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteScenario = async (scenarioId: string) => {
    if (!confirm("Are you sure you want to delete this scenario branch?")) return;
    try {
      await scenariosService.deleteScenario(scenarioId);
      fetchScenarios();
    } catch (err) {
      console.error("Delete scenario error:", err);
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading scenario register and probabilistic bounds..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchScenarios} />;
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Simulation trigger */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <GlobeIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Scenario Register & What-If Sandbox Simulations
            </h2>
            <p className="text-xs text-slate-400">
              Mutually consistent scenario families &bull; Probability bounds [low, high] &bull; Sibling family constraints
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
          >
            <PlusIcon className="w-3.5 h-3.5" />
            New Scenario
          </button>
          <button
            onClick={() => setIsSimOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            <SparklesIcon className="w-3.5 h-3.5" />
            Run What-If Simulation
          </button>
        </div>
      </div>

      {/* Scenarios List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {scenarios.map((scenario) => (
          <Card key={scenario.id} className="flex flex-col justify-between space-y-4 hover:border-slate-700 transition">
            <div>
              <div className="flex items-start justify-between gap-3 mb-2">
                <Badge variant="info" size="sm">
                  {scenario.scenario_family.replace("_", " ")}
                </Badge>
                <div className="flex items-center gap-1.5">
                  <Badge variant="neutral" size="sm">
                    {scenario.status}
                  </Badge>
                  <button
                    onClick={() => {
                      setEditingScenario(scenario);
                      setEditForm({
                        name: scenario.name,
                        scenario_family: scenario.scenario_family,
                        time_horizon: scenario.time_horizon,
                        description: scenario.description,
                        status: scenario.status,
                      });
                    }}
                    className="text-[10px] text-slate-400 hover:text-sky-400 font-mono"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteScenario(scenario.id)}
                    className="text-[10px] text-slate-500 hover:text-rose-400 font-mono"
                  >
                    <Trash2Icon className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <h3 className="text-sm font-bold text-slate-100 mb-1">{scenario.name}</h3>
              <p className="text-xs text-slate-400 line-clamp-3">
                {scenario.description || "Active geopolitical contingency pathway."}
              </p>
            </div>

            <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between font-mono">
              <span>HORIZON: {scenario.time_horizon}</span>
              <span className="capitalize text-slate-300">Scope: {scenario.scope_type}</span>
            </div>
          </Card>
        ))}

        {scenarios.length === 0 && (
          <div className="col-span-full py-12 text-center text-xs text-slate-500">
            No scenarios currently registered. Click &quot;New Scenario&quot; or &quot;Run What-If Simulation&quot; to begin.
          </div>
        )}
      </div>

      {/* What-If Simulation Sandbox Modal */}
      <Modal
        isOpen={isSimOpen}
        onClose={() => setIsSimOpen(false)}
        title="Hypothetical What-If Scenario Sandbox"
        subtitle="Simulate non-canonical geopolitical outcomes without altering production baseline records"
        maxWidth="4xl"
      >
        <div className="space-y-6">
          <form onSubmit={handleSimulate} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Scenario Family</label>
                <select
                  value={simForm.scenario_family}
                  onChange={(e) =>
                    setSimForm({ ...simForm, scenario_family: e.target.value as ScenarioFamily })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="rapid_escalation">Rapid Escalation</option>
                  <option value="status_quo">Status Quo</option>
                  <option value="de_escalation">De-escalation</option>
                  <option value="regime_crisis">Regime Crisis</option>
                  <option value="proxy_shift">Proxy Shift</option>
                  <option value="economic_collapse">Economic Collapse</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Scope</label>
                <select
                  value={simForm.scope_type}
                  onChange={(e) =>
                    setSimForm({ ...simForm, scope_type: e.target.value as ScopeType })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="regional">Regional Middle East</option>
                  <option value="country">Country Specific</option>
                  <option value="global">Global</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Time Horizon</label>
                <select
                  value={simForm.time_horizon}
                  onChange={(e) => setSimForm({ ...simForm, time_horizon: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="30_days">30 Days</option>
                  <option value="90_days">90 Days</option>
                  <option value="180_days">6 Months</option>
                  <option value="1_year">1 Year</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Hypothetical Context & Strategic Assumptions
              </label>
              <textarea
                rows={3}
                required
                placeholder="e.g. Direct kinetic strike against maritime tankers in Strait of Hormuz leads to retaliatory airstrikes and regional proxy mobilization..."
                value={simForm.hypothetical_context}
                onChange={(e) => setSimForm({ ...simForm, hypothetical_context: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500 leading-relaxed"
              />
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isSimulating || !simForm.hypothetical_context.trim()}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-xs font-semibold text-white rounded-lg transition flex items-center gap-1.5"
              >
                {isSimulating ? (
                  <>
                    <ActivityIcon className="w-3.5 h-3.5 animate-spin" /> Running Simulation...
                  </>
                ) : (
                  <>
                    <SparklesIcon className="w-3.5 h-3.5" /> Execute Simulation
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Simulation Output Card */}
          {simResult && (
            <div className="p-4 bg-slate-950 rounded-xl border border-sky-800/40 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Badge variant="info">Simulation Complete</Badge>
                  <span className="text-xs text-slate-400 font-mono">
                    PROBABILITY: {Math.round(simResult.probability_low * 100)}% – {Math.round(simResult.probability_high * 100)}%
                  </span>
                </div>
                <span className="text-xs text-slate-400 font-mono">
                  Confidence: {Math.round(simResult.confidence * 100)}%
                </span>
              </div>

              {simResult.explanation_of_change && (
                <div>
                  <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono mb-1">
                    Simulation Assessment
                  </h5>
                  <p className="text-xs text-slate-200 leading-relaxed">
                    {simResult.explanation_of_change}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {simResult.military_consequences && (
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                    <h6 className="text-[10px] font-bold uppercase text-rose-400 font-mono mb-1">
                      Military Consequences
                    </h6>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {simResult.military_consequences}
                    </p>
                  </div>
                )}
                {simResult.economic_consequences && (
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                    <h6 className="text-[10px] font-bold uppercase text-amber-400 font-mono mb-1">
                      Economic & Energy Consequences
                    </h6>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {simResult.economic_consequences}
                    </p>
                  </div>
                )}
              </div>

              {simResult.trigger_events.length > 0 && (
                <div>
                  <h6 className="text-[10px] font-bold uppercase text-slate-400 font-mono mb-1.5">
                    Critical Trigger Events
                  </h6>
                  <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                    {simResult.trigger_events.map((t, i) => (
                      <li key={i}>{t}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </Modal>

      {/* Create Scenario Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Register New Scenario"
        subtitle="Add a canonical scenario family entry to the intelligence database"
        maxWidth="md"
      >
        <form onSubmit={handleCreateScenario} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Scenario Title</label>
            <input
              type="text"
              required
              placeholder="e.g. Hormuz Blockade and Kinetic Retaliation"
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Scenario Family</label>
              <select
                value={createForm.scenario_family}
                onChange={(e) =>
                  setCreateForm({ ...createForm, scenario_family: e.target.value as ScenarioFamily })
                }
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="status_quo">Status Quo</option>
                <option value="rapid_escalation">Rapid Escalation</option>
                <option value="de_escalation">De-escalation</option>
                <option value="regime_crisis">Regime Crisis</option>
                <option value="proxy_shift">Proxy Shift</option>
                <option value="economic_collapse">Economic Collapse</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Time Horizon</label>
              <input
                type="text"
                placeholder="e.g. 90_days"
                value={createForm.time_horizon}
                onChange={(e) => setCreateForm({ ...createForm, time_horizon: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
            <textarea
              rows={3}
              placeholder="Detailed description of key conditions and trajectory..."
              value={createForm.description || ""}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
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
              {isCreating ? "Saving..." : "Create Scenario"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Scenario Modal */}
      {editingScenario && (
        <Modal
          isOpen={!!editingScenario}
          onClose={() => setEditingScenario(null)}
          title={`Edit Scenario: ${editingScenario.name}`}
          subtitle="Modify scenario parameters, family classification, and status"
          maxWidth="md"
        >
          <form onSubmit={handleUpdateScenario} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Scenario Title</label>
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
                <label className="block text-xs font-medium text-slate-300 mb-1">Scenario Family</label>
                <select
                  value={editForm.scenario_family || editingScenario.scenario_family}
                  onChange={(e) =>
                    setEditForm({ ...editForm, scenario_family: e.target.value as ScenarioFamily })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="status_quo">Status Quo</option>
                  <option value="rapid_escalation">Rapid Escalation</option>
                  <option value="de_escalation">De-escalation</option>
                  <option value="regime_crisis">Regime Crisis</option>
                  <option value="proxy_shift">Proxy Shift</option>
                  <option value="economic_collapse">Economic Collapse</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Status</label>
                <select
                  value={editForm.status || editingScenario.status}
                  onChange={(e) =>
                    setEditForm({ ...editForm, status: e.target.value as ScenarioStatus })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="active">Active</option>
                  <option value="dormant">Dormant</option>
                  <option value="realized">Realized</option>
                  <option value="invalidated">Invalidated</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Time Horizon</label>
              <input
                type="text"
                value={editForm.time_horizon || ""}
                onChange={(e) => setEditForm({ ...editForm, time_horizon: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
              <textarea
                rows={3}
                value={editForm.description || ""}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setEditingScenario(null)}
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

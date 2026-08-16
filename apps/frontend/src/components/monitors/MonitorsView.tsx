"use client";

import React, { useState, useEffect } from "react";
import { Monitor, CreateMonitorRequest, UpdateMonitorRequest } from "../../types";
import { monitorsService } from "../../services";
import {
  BellIcon,
  PlusIcon,
  RefreshCwIcon,
  Trash2Icon,
} from "../common/Icons";
import { Card } from "../common/Card";
import { Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function MonitorsView() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create Monitor Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState<CreateMonitorRequest>({
    name: "",
    monitor_type: "country_risk",
    condition_json: { threshold: 75, risk_code: "interstate_war" },
    delivery_channel: "telegram",
    enabled: true,
  });
  const [thresholdVal, setThresholdVal] = useState<number>(75);
  const [targetCode, setTargetCode] = useState<string>("interstate_war");
  const [isCreating, setIsCreating] = useState(false);

  // Edit Monitor Modal
  const [editingMonitor, setEditingMonitor] = useState<Monitor | null>(null);
  const [editForm, setEditForm] = useState<UpdateMonitorRequest>({});
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchMonitors = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await monitorsService.listMonitors();
      setMonitors(data);
    } catch (err) {
      console.error("Monitors fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load monitors");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitors();
  }, []);

  const handleToggle = async (monitor: Monitor) => {
    try {
      await monitorsService.updateMonitor(monitor.id, { enabled: !monitor.enabled });
      fetchMonitors();
    } catch (err) {
      console.error("Toggle monitor error:", err);
    }
  };

  const handleDelete = async (monitorId: string) => {
    if (!confirm("Are you sure you want to delete this alert monitor?")) return;
    try {
      await monitorsService.deleteMonitor(monitorId);
      fetchMonitors();
    } catch (err) {
      console.error("Delete monitor error:", err);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.name.trim()) return;

    setIsCreating(true);
    try {
      await monitorsService.createMonitor({
        ...createForm,
        condition_json: {
          threshold: Number(thresholdVal),
          code: targetCode.trim(),
        },
      });
      setIsCreateOpen(false);
      setCreateForm({
        name: "",
        monitor_type: "country_risk",
        condition_json: {},
        delivery_channel: "telegram",
        enabled: true,
      });
      fetchMonitors();
    } catch (err) {
      console.error("Create monitor error:", err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingMonitor) return;

    setIsUpdating(true);
    try {
      await monitorsService.updateMonitor(editingMonitor.id, editForm);
      setEditingMonitor(null);
      fetchMonitors();
    } catch (err) {
      console.error("Update monitor error:", err);
    } finally {
      setIsUpdating(false);
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading alert monitor registry and threshold triggers..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchMonitors} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <BellIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Automated Monitors & Real-Time Alert Dispatch
            </h2>
            <p className="text-xs text-slate-400">
              Continuous background polling &bull; Escalation threshold triggers &bull; Multi-channel notification delivery
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchMonitors}
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
            New Monitor
          </button>
        </div>
      </div>

      {/* Monitors List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {monitors.map((m) => (
          <Card key={m.id} className="flex flex-col justify-between space-y-4 hover:border-slate-700 transition">
            <div>
              <div className="flex items-start justify-between gap-3 mb-2">
                <Badge variant={m.enabled ? "success" : "neutral"} size="sm">
                  {m.enabled ? "ACTIVE" : "DISABLED"}
                </Badge>
                <div className="flex items-center gap-1.5">
                  <Badge variant="info" size="sm">
                    {m.delivery_channel}
                  </Badge>
                  <button
                    onClick={() => {
                      setEditingMonitor(m);
                      setEditForm({
                        name: m.name,
                        delivery_channel: m.delivery_channel,
                        enabled: m.enabled,
                      });
                    }}
                    className="text-[10px] text-slate-400 hover:text-sky-400 font-mono"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(m.id)}
                    className="text-slate-500 hover:text-rose-400 p-1"
                    title="Delete"
                  >
                    <Trash2Icon className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <h3 className="text-sm font-bold text-slate-100 mb-1">{m.name}</h3>

              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 space-y-1">
                <span className="text-[10px] text-slate-500 uppercase font-bold block">
                  Rule Trigger Condition:
                </span>
                <pre className="text-[11px] overflow-x-auto text-sky-400">
                  {JSON.stringify(m.condition_json, null, 2)}
                </pre>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
              <span className="text-[10px] text-slate-500 font-mono">
                {m.last_triggered_at
                  ? `Triggered: ${new Date(m.last_triggered_at).toLocaleDateString()}`
                  : "Never triggered"}
              </span>

              <button
                onClick={() => handleToggle(m)}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition ${
                  m.enabled
                    ? "bg-slate-800 hover:bg-slate-700 text-slate-300"
                    : "bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-800"
                }`}
              >
                {m.enabled ? "Disable" : "Enable"}
              </button>
            </div>
          </Card>
        ))}

        {monitors.length === 0 && (
          <div className="col-span-full py-12 text-center text-xs text-slate-500">
            No active monitors configured. Click &quot;New Monitor&quot; to set up threshold alert rules.
          </div>
        )}
      </div>

      {/* Create Monitor Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create Automated Alert Monitor"
        subtitle="Set up background condition evaluations with automated webhook or notification alerts"
        maxWidth="md"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Monitor Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Red Sea Maritime Threat Spike Warning"
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Monitor Type</label>
              <select
                value={createForm.monitor_type}
                onChange={(e) => setCreateForm({ ...createForm, monitor_type: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="country_risk">Country Risk Threshold</option>
                <option value="relationship_threshold">Relationship Escalation</option>
                <option value="keyword_trigger">Keyword Event Trigger</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Delivery Channel
              </label>
              <select
                value={createForm.delivery_channel}
                onChange={(e) => setCreateForm({ ...createForm, delivery_channel: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="telegram">Telegram Dispatch</option>
                <option value="webhook">Webhook HTTP Post</option>
                <option value="email">Analyst Email</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Target Code / Key</label>
              <input
                type="text"
                placeholder="e.g. maritime_disruption"
                value={targetCode}
                onChange={(e) => setTargetCode(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Score Threshold (&gt;= {thresholdVal})
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={thresholdVal}
                onChange={(e) => setThresholdVal(Number(e.target.value))}
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
              {isCreating ? "Saving..." : "Create Monitor"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Monitor Modal */}
      {editingMonitor && (
        <Modal
          isOpen={!!editingMonitor}
          onClose={() => setEditingMonitor(null)}
          title={`Edit Monitor: ${editingMonitor.name}`}
          subtitle="Modify alert dispatch settings and name"
          maxWidth="md"
        >
          <form onSubmit={handleUpdate} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Monitor Name</label>
              <input
                type="text"
                required
                value={editForm.name || ""}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Delivery Channel
              </label>
              <select
                value={editForm.delivery_channel || editingMonitor.delivery_channel}
                onChange={(e) => setEditForm({ ...editForm, delivery_channel: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="telegram">Telegram Dispatch</option>
                <option value="webhook">Webhook HTTP Post</option>
                <option value="email">Analyst Email</option>
              </select>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="edit_mon_enabled"
                checked={editForm.enabled ?? editingMonitor.enabled}
                onChange={(e) => setEditForm({ ...editForm, enabled: e.target.checked })}
                className="rounded bg-slate-950 border-slate-800 text-sky-600 focus:ring-0"
              />
              <label htmlFor="edit_mon_enabled" className="text-xs text-slate-200">
                Active for automated threshold checking
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setEditingMonitor(null)}
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

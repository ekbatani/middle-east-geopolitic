"use client";

import React, { useState, useEffect } from "react";
import { ReviewItem, ReviewType, ReviewStatus, Actor } from "../../types";
import { reviewService, actorsService } from "../../services";
import {
  CheckCircleIcon,
  XCircleIcon,
  RefreshCwIcon,
  ActivityIcon,
  ShieldIcon,
  UserIcon,
} from "../common/Icons";
import { Card, CardHeader } from "../common/Card";
import { Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function ReviewQueueView() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [actors, setActors] = useState<Actor[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState<ReviewType | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState<ReviewStatus>("pending");

  // Entity Resolution Modal
  const [resolvingItem, setResolvingItem] = useState<ReviewItem | null>(null);
  const [selectedActorId, setSelectedActorId] = useState<string>("");
  const [isResolving, setIsResolving] = useState(false);

  // Acknowledge Modal
  const [acknowledgingItem, setAcknowledgingItem] = useState<ReviewItem | null>(null);
  const [ackNote, setAckNote] = useState("");
  const [isAcking, setIsAcking] = useState(false);

  const fetchQueue = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [queueData, actorsData] = await Promise.all([
        reviewService.listPending({
          review_type: typeFilter,
          status: statusFilter,
        }),
        actorsService.listActors({ limit: 100 }),
      ]);
      setItems(queueData);
      setActors(actorsData);
      if (actorsData.length > 0 && !selectedActorId) {
        setSelectedActorId(actorsData[0].id);
      }
    } catch (err) {
      console.error("Review queue fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load review queue");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [typeFilter, statusFilter]);

  const handleResolveEntity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingItem || !selectedActorId) return;

    setIsResolving(true);
    try {
      await reviewService.resolveEntityResolution(resolvingItem.id, {
        resolved_actor_id: selectedActorId,
      });
      setResolvingItem(null);
      fetchQueue();
    } catch (err) {
      console.error("Resolve error:", err);
    } finally {
      setIsResolving(false);
    }
  };

  const handleAcknowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!acknowledgingItem) return;

    setIsAcking(true);
    try {
      await reviewService.acknowledgeHighImpactEvent(acknowledgingItem.id, {
        note: ackNote.trim() || undefined,
      });
      setAcknowledgingItem(null);
      setAckNote("");
      fetchQueue();
    } catch (err) {
      console.error("Acknowledge error:", err);
    } finally {
      setIsAcking(false);
    }
  };

  const handleReject = async (itemId: string) => {
    try {
      await reviewService.rejectReviewItem(itemId);
      fetchQueue();
    } catch (err) {
      console.error("Reject review item error:", err);
    }
  };

  if (isLoading && items.length === 0) {
    return <LoadingState message="Loading analyst review queue and pending entity disambiguations..." />;
  }

  if (error && items.length === 0) {
    return <ErrorState message={error} onRetry={fetchQueue} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <CheckCircleIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Analyst Verification & Disambiguation Queue
            </h2>
            <p className="text-xs text-slate-400">
              Human-in-the-loop validation &bull; Entity resolution matches &bull; Critical event acknowledgement
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <select
            value={typeFilter || ""}
            onChange={(e) =>
              setTypeFilter(e.target.value ? (e.target.value as ReviewType) : undefined)
            }
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 cursor-pointer"
          >
            <option value="" className="bg-slate-900">All Review Types</option>
            <option value="entity_resolution" className="bg-slate-900">Entity Resolution</option>
            <option value="high_impact_event" className="bg-slate-900">High-Impact Event</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ReviewStatus)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 cursor-pointer"
          >
            <option value="pending" className="bg-slate-900">Pending Action</option>
            <option value="resolved" className="bg-slate-900">Resolved</option>
            <option value="rejected" className="bg-slate-900">Rejected</option>
          </select>

          <button
            onClick={fetchQueue}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCwIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Review Queue Items */}
      <div className="space-y-4">
        {items.map((item) => {
          const isEntity = item.review_type === "entity_resolution";
          const isPending = item.status === "pending";

          return (
            <Card
              key={item.id}
              className="p-5 bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Badge variant={isEntity ? "info" : "critical"}>
                    {isEntity ? "Entity Resolution" : "High-Impact Event"}
                  </Badge>
                  <Badge
                    variant={
                      item.status === "resolved"
                        ? "success"
                        : item.status === "rejected"
                        ? "danger"
                        : "warning"
                    }
                  >
                    {item.status}
                  </Badge>
                </div>

                <span className="text-[11px] font-mono text-slate-500">
                  Item ID: {item.id.slice(0, 8)} &bull; Created:{" "}
                  {new Date(item.created_at).toLocaleString()}
                </span>
              </div>

              {/* Subject Payload details */}
              <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 space-y-1.5">
                <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block">
                  Subject Context:
                </span>
                <pre className="text-xs text-slate-200 font-mono whitespace-pre-wrap">
                  {JSON.stringify(item.subject_json, null, 2)}
                </pre>
              </div>

              {/* Candidates preview if entity resolution */}
              {isEntity && item.candidates_json.length > 0 && (
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block mb-1">
                    Candidate Matches:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {item.candidates_json.map((c, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 bg-slate-900 rounded-lg border border-slate-800 text-xs text-sky-300 font-mono"
                      >
                        {typeof c === "object" ? JSON.stringify(c) : String(c)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Resolution details if already resolved */}
              {item.resolution_json && (
                <div className="p-2.5 bg-emerald-950/20 border border-emerald-800/40 rounded-lg text-xs text-emerald-300 font-mono">
                  Resolution: {JSON.stringify(item.resolution_json)}
                </div>
              )}

              {/* Action buttons if pending */}
              {isPending && (
                <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                  <button
                    onClick={() => handleReject(item.id)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-rose-950 text-slate-300 hover:text-rose-300 text-xs font-semibold rounded-lg border border-slate-700 transition"
                  >
                    Reject Item
                  </button>

                  {isEntity ? (
                    <button
                      onClick={() => {
                        setResolvingItem(item);
                        if (actors.length > 0) setSelectedActorId(actors[0].id);
                      }}
                      className="px-4 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-1.5"
                    >
                      <UserIcon className="w-3.5 h-3.5" />
                      Resolve Entity
                    </button>
                  ) : (
                    <button
                      onClick={() => {
                        setAcknowledgingItem(item);
                        setAckNote("");
                      }}
                      className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-1.5"
                    >
                      <CheckCircleIcon className="w-3.5 h-3.5" />
                      Acknowledge Event
                    </button>
                  )}
                </div>
              )}
            </Card>
          );
        })}

        {items.length === 0 && (
          <div className="py-16 text-center text-xs text-slate-500 bg-slate-950 rounded-2xl border border-slate-800">
            <CheckCircleIcon className="w-8 h-8 text-emerald-500/50 mx-auto mb-2" />
            No pending items in analyst review queue. All candidate entities and high-impact events have been processed.
          </div>
        )}
      </div>

      {/* Entity Resolution Modal */}
      {resolvingItem && (
        <Modal
          isOpen={!!resolvingItem}
          onClose={() => setResolvingItem(null)}
          title="Resolve Entity Disambiguation"
          subtitle="Map the candidate mention to the official canonical Actor record"
          maxWidth="md"
        >
          <form onSubmit={handleResolveEntity} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Select Canonical Actor
              </label>
              <select
                value={selectedActorId}
                onChange={(e) => setSelectedActorId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                {actors.map((a) => (
                  <option key={a.id} value={a.id} className="bg-slate-900">
                    {a.canonical_name} ({a.actor_type})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setResolvingItem(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isResolving}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition"
              >
                {isResolving ? "Resolving..." : "Confirm Resolution"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Acknowledge Event Modal */}
      {acknowledgingItem && (
        <Modal
          isOpen={!!acknowledgingItem}
          onClose={() => setAcknowledgingItem(null)}
          title="Acknowledge High-Impact Event"
          subtitle="Confirm review of critical escalation threshold"
          maxWidth="md"
        >
          <form onSubmit={handleAcknowledge} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Analyst Verification Note (Optional)
              </label>
              <textarea
                rows={3}
                placeholder="e.g. Verified with command staff; kinetic impact confirmed in maritime transit corridor..."
                value={ackNote}
                onChange={(e) => setAckNote(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500 leading-relaxed"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setAcknowledgingItem(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isAcking}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition"
              >
                {isAcking ? "Acknowledging..." : "Confirm Acknowledgement"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

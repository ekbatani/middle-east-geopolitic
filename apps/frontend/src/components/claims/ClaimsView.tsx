"use client";

import React, { useState, useEffect } from "react";
import {
  Claim,
  ClaimEvidence,
  CreateClaimRequest,
  UpdateClaimRequest,
  AddClaimEvidenceRequest,
  EvidenceStance,
  Document,
  VerificationStatus,
  LifecycleStatus,
} from "../../types";
import { claimsService, documentsService } from "../../services";
import {
  ShieldIcon,
  PlusIcon,
  RefreshCwIcon,
  Trash2Icon,
} from "../common/Icons";
import { Card } from "../common/Card";
import { Badge, VerificationBadge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function ClaimsView() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [evidenceList, setEvidenceList] = useState<ClaimEvidence[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create Claim Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState<CreateClaimRequest>({
    claim_text: "",
    claim_type: "kinetic_assertion",
  });
  const [isCreating, setIsCreating] = useState(false);

  // Edit Claim Modal
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editForm, setEditForm] = useState<UpdateClaimRequest>({});
  const [isUpdating, setIsUpdating] = useState(false);

  // Add Evidence Modal
  const [isAddEvidenceOpen, setIsAddEvidenceOpen] = useState(false);
  const [evidenceForm, setEvidenceForm] = useState<AddClaimEvidenceRequest>({
    document_id: "",
    stance: "supports",
    excerpt: "",
    confidence: 0.85,
    analyst_note: "",
  });
  const [isAddingEvidence, setIsAddingEvidence] = useState(false);

  const fetchClaims = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [claimsData, docsData] = await Promise.all([
        claimsService.listClaims({ limit: 100 }),
        documentsService.listDocuments({ limit: 50 }),
      ]);
      setClaims(claimsData);
      setDocuments(docsData);
      if (docsData.length > 0 && !evidenceForm.document_id) {
        setEvidenceForm((prev) => ({ ...prev, document_id: docsData[0].id }));
      }
    } catch (err) {
      console.error("Claims fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load claims");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchClaims();
  }, []);

  const handleSelectClaim = async (claim: Claim) => {
    setSelectedClaim(claim);
    setLoadingEvidence(true);
    try {
      const ev = await claimsService.getClaimEvidence(claim.id);
      setEvidenceList(ev);
    } catch (err) {
      console.error("Evidence error:", err);
    } finally {
      setLoadingEvidence(false);
    }
  };

  const handleCreateClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.claim_text.trim()) return;

    setIsCreating(true);
    try {
      const created = await claimsService.createClaim(createForm);
      setIsCreateOpen(false);
      setCreateForm({ claim_text: "", claim_type: "kinetic_assertion" });
      fetchClaims();
      setSelectedClaim(created);
    } catch (err) {
      console.error("Create claim error:", err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClaim) return;
    setIsUpdating(true);
    try {
      const updated = await claimsService.updateClaim(selectedClaim.id, editForm);
      setIsEditOpen(false);
      setSelectedClaim(updated);
      fetchClaims();
    } catch (err) {
      console.error("Update claim error:", err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteClaim = async (claimId: string) => {
    if (!confirm("Are you sure you want to delete this claim and all associated verification links?")) return;
    try {
      await claimsService.deleteClaim(claimId);
      if (selectedClaim?.id === claimId) {
        setSelectedClaim(null);
        setEvidenceList([]);
      }
      fetchClaims();
    } catch (err) {
      console.error("Delete claim error:", err);
    }
  };

  const handleAddEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClaim || !evidenceForm.document_id || !evidenceForm.excerpt.trim()) return;

    setIsAddingEvidence(true);
    try {
      await claimsService.addClaimEvidence(selectedClaim.id, evidenceForm);
      setIsAddEvidenceOpen(false);
      setEvidenceForm({
        document_id: documents.length > 0 ? documents[0].id : "",
        stance: "supports",
        excerpt: "",
        confidence: 0.85,
        analyst_note: "",
      });
      // Refresh evidence
      const ev = await claimsService.getClaimEvidence(selectedClaim.id);
      setEvidenceList(ev);
    } catch (err) {
      console.error("Add evidence error:", err);
    } finally {
      setIsAddingEvidence(false);
    }
  };

  const handleDeleteEvidence = async (evidenceId: string) => {
    if (!selectedClaim) return;
    try {
      await claimsService.deleteClaimEvidence(evidenceId);
      const ev = await claimsService.getClaimEvidence(selectedClaim.id);
      setEvidenceList(ev);
    } catch (err) {
      console.error("Delete evidence error:", err);
    }
  };

  if (isLoading && claims.length === 0) {
    return <LoadingState message="Loading claims register and multi-document verification stances..." />;
  }

  if (error && claims.length === 0) {
    return <ErrorState message={error} onRetry={fetchClaims} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <ShieldIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Claims Register & Verification Evidence
            </h2>
            <p className="text-xs text-slate-400">
              Corroboration & debunking audit trail &bull; Supporting vs refuting document chunks &bull; Stance confidence scoring
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchClaims}
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
            New Claim
          </button>
        </div>
      </div>

      {/* Grid Layout: Claims List & Evidence Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Claims List */}
        <div className="space-y-3 max-h-[calc(100vh-16rem)] overflow-y-auto pr-1">
          {claims.map((claim) => {
            const isSelected = selectedClaim?.id === claim.id;
            return (
              <div
                key={claim.id}
                onClick={() => handleSelectClaim(claim)}
                className={`p-4 rounded-xl border cursor-pointer transition space-y-2 ${
                  isSelected
                    ? "bg-slate-900 border-sky-500 shadow-md ring-1 ring-sky-500/20"
                    : "bg-slate-950/60 hover:bg-slate-900 border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between">
                  <VerificationBadge status={claim.verification_status} />
                  <Badge variant="neutral" size="sm">
                    {claim.claim_type}
                  </Badge>
                </div>

                <h4 className="text-xs font-semibold text-slate-100 line-clamp-3 leading-relaxed">
                  &ldquo;{claim.claim_text}&rdquo;
                </h4>

                <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1">
                  <span>Confidence: {claim.confidence ? `${Math.round(claim.confidence * 100)}%` : "Unrated"}</span>
                  <span className="capitalize text-slate-400">Status: {claim.lifecycle_status}</span>
                </div>
              </div>
            );
          })}

          {claims.length === 0 && (
            <div className="py-12 text-center text-xs text-slate-500">
              No claims in database. Click &quot;New Claim&quot; to log an assertion.
            </div>
          )}
        </div>

        {/* Right 2 Columns: Selected Claim Details & Evidence Bundles */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="h-full flex flex-col justify-between">
            {selectedClaim ? (
              <div className="space-y-6">
                {/* Header */}
                <div className="border-b border-slate-800 pb-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <VerificationBadge status={selectedClaim.verification_status} />
                      <Badge variant="neutral">{selectedClaim.lifecycle_status}</Badge>
                      <span className="text-xs text-slate-400 font-mono">
                        Conf: {selectedClaim.confidence ? `${Math.round(selectedClaim.confidence * 100)}%` : "N/A"}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          setEditForm({
                            claim_text: selectedClaim.claim_text,
                            claim_type: selectedClaim.claim_type,
                            verification_status: selectedClaim.verification_status,
                            lifecycle_status: selectedClaim.lifecycle_status,
                            confidence: selectedClaim.confidence,
                          });
                          setIsEditOpen(true);
                        }}
                        className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 font-medium rounded-lg border border-slate-700 transition"
                      >
                        Edit Claim
                      </button>

                      <button
                        onClick={() => setIsAddEvidenceOpen(true)}
                        className="px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-1"
                      >
                        <PlusIcon className="w-3.5 h-3.5" />
                        Attach Evidence
                      </button>

                      <button
                        onClick={() => handleDeleteClaim(selectedClaim.id)}
                        className="p-1 bg-rose-950/40 hover:bg-rose-900 border border-rose-800 text-rose-300 rounded-lg transition"
                        title="Delete Claim"
                      >
                        <Trash2Icon className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <p className="text-sm font-semibold text-slate-100 bg-slate-950 p-3.5 rounded-xl border border-slate-800 leading-relaxed">
                    &ldquo;{selectedClaim.claim_text}&rdquo;
                  </p>
                </div>

                {/* Evidence Stances List */}
                <div>
                  <h5 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono mb-3">
                    Attached Verification Evidence ({evidenceList.length} Items)
                  </h5>

                  {loadingEvidence ? (
                    <LoadingState message="Fetching supporting & refuting document excerpts..." />
                  ) : evidenceList.length > 0 ? (
                    <div className="space-y-3">
                      {evidenceList.map((ev) => {
                        const isSupports = ev.stance === "supports";
                        const isRefutes = ev.stance === "refutes";
                        return (
                          <div
                            key={ev.id}
                            className={`p-3.5 rounded-xl border space-y-2 ${
                              isSupports
                                ? "bg-emerald-950/20 border-emerald-800/40"
                                : isRefutes
                                ? "bg-rose-950/20 border-rose-800/40"
                                : "bg-slate-950 border-slate-800"
                            }`}
                          >
                            <div className="flex items-center justify-between text-xs">
                              <Badge
                                variant={
                                  isSupports ? "success" : isRefutes ? "danger" : "neutral"
                                }
                                size="sm"
                              >
                                Stance: {ev.stance}
                              </Badge>

                              <div className="flex items-center gap-3">
                                <span className="text-[10px] text-slate-500 font-mono">
                                  Conf: {ev.confidence ? `${Math.round(ev.confidence * 100)}%` : "N/A"} &bull;{" "}
                                  {new Date(ev.created_at).toLocaleDateString()}
                                </span>
                                <button
                                  onClick={() => handleDeleteEvidence(ev.id)}
                                  className="text-slate-500 hover:text-rose-400 text-xs"
                                  title="Remove evidence link"
                                >
                                  &times; Remove
                                </button>
                              </div>
                            </div>

                            <p className="text-xs text-slate-200 leading-relaxed font-sans italic bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
                              &ldquo;{ev.excerpt}&rdquo;
                            </p>

                            {ev.analyst_note && (
                              <div className="text-[11px] text-slate-400 font-mono">
                                Note: {ev.analyst_note}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="py-8 text-center text-xs text-slate-500 bg-slate-950 rounded-xl border border-slate-800">
                      No document evidence attached yet. Click &quot;Attach Evidence&quot; to link source chunks.
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-24 text-center text-slate-500 text-xs flex flex-col items-center justify-center">
                <ShieldIcon className="w-8 h-8 text-slate-600 mb-2" />
                Select a claim from the left panel to inspect attached verification evidence and stance breakdowns.
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Create Claim Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Register Assertion / Claim"
        subtitle="Log an unverified or disputed claim to initiate corroboration workflows"
        maxWidth="md"
      >
        <form onSubmit={handleCreateClaim} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Claim Text</label>
            <textarea
              rows={3}
              required
              placeholder="e.g. State media reports anti-ship ballistic missile was launched from coastal battery in Hodeidah..."
              value={createForm.claim_text}
              onChange={(e) => setCreateForm({ ...createForm, claim_text: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500 leading-relaxed"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Claim Type</label>
            <select
              value={createForm.claim_type}
              onChange={(e) => setCreateForm({ ...createForm, claim_type: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="kinetic_assertion">Kinetic / Strike Assertion</option>
              <option value="casualty_claim">Casualty / Damage Report</option>
              <option value="diplomatic_position">Diplomatic Stance</option>
              <option value="attribution_statement">Responsibility Attribution</option>
            </select>
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
              {isCreating ? "Saving..." : "Create Claim"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Claim Modal */}
      {selectedClaim && (
        <Modal
          isOpen={isEditOpen}
          onClose={() => setIsEditOpen(false)}
          title="Edit Claim Details & Status"
          subtitle="Update assertion text, verification stance, and confidence"
          maxWidth="md"
        >
          <form onSubmit={handleUpdateClaim} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Claim Text</label>
              <textarea
                rows={3}
                required
                value={editForm.claim_text || ""}
                onChange={(e) => setEditForm({ ...editForm, claim_text: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500 leading-relaxed"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Verification Status</label>
                <select
                  value={editForm.verification_status || selectedClaim.verification_status}
                  onChange={(e) =>
                    setEditForm({ ...editForm, verification_status: e.target.value as VerificationStatus })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="unverified">Unverified</option>
                  <option value="disputed">Disputed</option>
                  <option value="verified">Verified</option>
                  <option value="debunked">Debunked</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Lifecycle Status</label>
                <select
                  value={editForm.lifecycle_status || selectedClaim.lifecycle_status}
                  onChange={(e) =>
                    setEditForm({ ...editForm, lifecycle_status: e.target.value as LifecycleStatus })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Confidence Score (0.0 - 1.0)</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={editForm.confidence ?? selectedClaim.confidence ?? 0.5}
                onChange={(e) =>
                  setEditForm({ ...editForm, confidence: Number(e.target.value) })
                }
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsEditOpen(false)}
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

      {/* Add Evidence Modal */}
      <Modal
        isOpen={isAddEvidenceOpen}
        onClose={() => setIsAddEvidenceOpen(false)}
        title="Attach Document Evidence to Claim"
        subtitle="Link supporting or refuting source excerpt with analyst stance"
        maxWidth="md"
      >
        <form onSubmit={handleAddEvidence} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Source Document</label>
            <select
              value={evidenceForm.document_id}
              onChange={(e) => setEvidenceForm({ ...evidenceForm, document_id: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id} className="bg-slate-900">
                  {d.title || d.canonical_url}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Stance</label>
              <select
                value={evidenceForm.stance}
                onChange={(e) =>
                  setEvidenceForm({ ...evidenceForm, stance: e.target.value as EvidenceStance })
                }
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="supports">Supports Claim</option>
                <option value="refutes">Refutes / Contradicts Claim</option>
                <option value="neutral">Neutral / Informational</option>
                <option value="context">Contextual Background</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Confidence</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={evidenceForm.confidence || 0.85}
                onChange={(e) =>
                  setEvidenceForm({ ...evidenceForm, confidence: Number(e.target.value) })
                }
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Excerpt Quote</label>
            <textarea
              rows={3}
              required
              placeholder="Exact verbatim sentence from source document..."
              value={evidenceForm.excerpt}
              onChange={(e) => setEvidenceForm({ ...evidenceForm, excerpt: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500 leading-relaxed font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Analyst Note</label>
            <input
              type="text"
              placeholder="e.g. Cross-verified with satellite infrared thermal detection..."
              value={evidenceForm.analyst_note || ""}
              onChange={(e) => setEvidenceForm({ ...evidenceForm, analyst_note: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsAddEvidenceOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isAddingEvidence}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition"
            >
              {isAddingEvidence ? "Attaching..." : "Attach Evidence"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

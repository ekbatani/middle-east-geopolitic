"use client";

import React, { useState, useEffect } from "react";
import {
  Source,
  Document,
  SourceType,
  EndpointType,
  CreateSourceRequest,
  UpdateSourceRequest,
  CreateSourceEndpointRequest,
  SubmitSourceRequest,
  SubmitSourceResponse,
} from "../../types";
import { sourcesService, documentsService } from "../../services";
import {
  DatabaseIcon,
  FileTextIcon,
  PlusIcon,
  ActivityIcon,
  RefreshCwIcon,
  CheckCircleIcon,
  GlobeIcon,
  Trash2Icon,
} from "../common/Icons";
import { Card, CardHeader } from "../common/Card";
import { Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function SourcesView() {
  const [sources, setSources] = useState<Source[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Ingest URL Modal
  const [isSubmitOpen, setIsSubmitOpen] = useState(false);
  const [submitForm, setSubmitForm] = useState<SubmitSourceRequest>({
    url: "",
    title: "",
  });
  const [submitResult, setSubmitResult] = useState<SubmitSourceResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Create Source Modal
  const [isCreateSourceOpen, setIsCreateSourceOpen] = useState(false);
  const [createSourceForm, setCreateSourceForm] = useState<CreateSourceRequest>({
    name: "",
    source_type: "news_outlet",
    base_url: "",
    default_language: "en",
  });
  const [isCreatingSource, setIsCreatingSource] = useState(false);

  // Edit Source Modal
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [editSourceForm, setEditSourceForm] = useState<UpdateSourceRequest>({});
  const [isUpdatingSource, setIsUpdatingSource] = useState(false);

  // Add Endpoint Modal
  const [endpointSourceId, setEndpointSourceId] = useState<string | null>(null);
  const [endpointForm, setEndpointForm] = useState<CreateSourceEndpointRequest>({
    endpoint_type: "rss",
    url: "",
    schedule: "critical",
  });
  const [isAddingEndpoint, setIsAddingEndpoint] = useState(false);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [sourcesData, docsData] = await Promise.all([
        sourcesService.listSources({ limit: 50 }),
        documentsService.listDocuments({ limit: 50 }),
      ]);
      setSources(sourcesData);
      setDocuments(docsData);
    } catch (err) {
      console.error("Sources fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load sources");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmitSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!submitForm.url.trim()) return;

    setIsSubmitting(true);
    setSubmitResult(null);
    try {
      const res = await sourcesService.submitSource(submitForm);
      setSubmitResult(res);
      setSubmitForm({ url: "", title: "" });
      fetchData();
    } catch (err) {
      console.error("Submit source error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createSourceForm.name.trim()) return;

    setIsCreatingSource(true);
    try {
      await sourcesService.createSource(createSourceForm);
      setIsCreateSourceOpen(false);
      setCreateSourceForm({
        name: "",
        source_type: "news_outlet",
        base_url: "",
        default_language: "en",
      });
      fetchData();
    } catch (err) {
      console.error("Create source error:", err);
    } finally {
      setIsCreatingSource(false);
    }
  };

  const handleUpdateSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSource) return;

    setIsUpdatingSource(true);
    try {
      await sourcesService.updateSource(editingSource.id, editSourceForm);
      setEditingSource(null);
      fetchData();
    } catch (err) {
      console.error("Update source error:", err);
    } finally {
      setIsUpdatingSource(false);
    }
  };

  const handleDeleteSource = async (sourceId: string) => {
    if (!confirm("Are you sure you want to delete this source and all its endpoints?")) return;
    try {
      await sourcesService.deleteSource(sourceId);
      fetchData();
    } catch (err) {
      console.error("Delete source error:", err);
    }
  };

  const handleAddEndpoint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!endpointSourceId || !endpointForm.url.trim()) return;

    setIsAddingEndpoint(true);
    try {
      await sourcesService.addSourceEndpoint(endpointSourceId, endpointForm);
      setEndpointSourceId(null);
      setEndpointForm({ endpoint_type: "rss", url: "", schedule: "critical" });
      fetchData();
    } catch (err) {
      console.error("Add endpoint error:", err);
    } finally {
      setIsAddingEndpoint(false);
    }
  };

  const handleDeleteEndpoint = async (endpointId: string) => {
    if (!confirm("Are you sure you want to delete this collection endpoint?")) return;
    try {
      await sourcesService.deleteSourceEndpoint(endpointId);
      fetchData();
    } catch (err) {
      console.error("Delete endpoint error:", err);
    }
  };

  if (isLoading && sources.length === 0 && documents.length === 0) {
    return <LoadingState message="Connecting to intelligence feeds and document archive..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <DatabaseIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Intelligence Sources & Document Ingestion
            </h2>
            <p className="text-xs text-slate-400">
              Automated collectors &bull; Web archiving & MinIO object storage &bull; Clean text extraction & chunking
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={fetchData}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCwIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsCreateSourceOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition"
          >
            <PlusIcon className="w-4 h-4" />
            Register Feed
          </button>
          <button
            onClick={() => {
              setIsSubmitOpen(true);
              setSubmitResult(null);
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            <PlusIcon className="w-4 h-4" />
            Ingest Source URL
          </button>
        </div>
      </div>

      {/* Grid: Registered Feeds & Document Archive */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Registered Sources / Feeds */}
        <div className="space-y-4">
          <Card>
            <CardHeader
              title="Registered Feeds & Collectors"
              subtitle={`${sources.length} active collection streams`}
              icon={<GlobeIcon className="w-5 h-5" />}
            />

            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {sources.map((s) => (
                <div
                  key={s.id}
                  className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-xl space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">{s.name}</span>
                    <div className="flex items-center gap-1.5">
                      <Badge variant={s.enabled ? "success" : "neutral"} size="sm">
                        {s.source_type}
                      </Badge>
                      <button
                        onClick={() => {
                          setEditingSource(s);
                          setEditSourceForm({
                            name: s.name,
                            source_type: s.source_type,
                            base_url: s.base_url,
                            default_language: s.default_language,
                            enabled: s.enabled,
                          });
                        }}
                        className="text-[10px] text-slate-400 hover:text-sky-400 font-mono"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteSource(s.id)}
                        className="text-[10px] text-slate-500 hover:text-rose-400 font-mono"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  {s.base_url && (
                    <a
                      href={s.base_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[11px] text-sky-400 hover:underline font-mono truncate block"
                    >
                      {s.base_url}
                    </a>
                  )}

                  {/* Endpoints */}
                  {s.endpoints && s.endpoints.length > 0 && (
                    <div className="space-y-1.5 pt-1.5 border-t border-slate-900">
                      <div className="text-[10px] font-bold text-slate-500 uppercase font-mono">
                        Endpoints ({s.endpoints.length})
                      </div>
                      {s.endpoints.map((ep) => (
                        <div
                          key={ep.id}
                          className="p-2 bg-slate-900/80 rounded border border-slate-800/80 flex items-center justify-between text-[11px]"
                        >
                          <div className="truncate max-w-[170px]">
                            <span className="text-[9px] uppercase font-mono px-1 py-0.5 bg-slate-800 text-sky-300 rounded mr-1">
                              {ep.endpoint_type}
                            </span>
                            <span className="text-slate-300 font-mono truncate">{ep.url}</span>
                          </div>
                          <button
                            onClick={() => handleDeleteEndpoint(ep.id)}
                            className="text-slate-500 hover:text-rose-400 text-xs ml-1"
                            title="Remove endpoint"
                          >
                            &times;
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="pt-1 flex justify-end">
                    <button
                      onClick={() => setEndpointSourceId(s.id)}
                      className="text-[10px] text-sky-400 hover:underline font-mono"
                    >
                      + Add Endpoint URL
                    </button>
                  </div>
                </div>
              ))}

              {sources.length === 0 && (
                <div className="py-8 text-center text-xs text-slate-500">
                  No automated sources registered in database.
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right 2 Columns: Ingested Document Archive */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader
              title="Archived Documents & Extracted Chunks"
              subtitle={`${documents.length} ingested intelligence documents`}
              icon={<FileTextIcon className="w-5 h-5" />}
            />

            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => setSelectedDocument(doc)}
                  className="p-4 bg-slate-950/60 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl cursor-pointer transition space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <Badge variant="info" size="sm">
                      Status: {doc.status}
                    </Badge>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {doc.retrieved_at ? new Date(doc.retrieved_at).toLocaleString() : "Archived"}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-slate-100">
                    {doc.title || doc.canonical_url}
                  </h4>

                  {doc.extracted_text && (
                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                      {doc.extracted_text}
                    </p>
                  )}

                  <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1">
                    <span className="truncate max-w-sm">{doc.canonical_url}</span>
                    <span>{doc.chunks.length} extracted chunks</span>
                  </div>
                </div>
              ))}

              {documents.length === 0 && (
                <div className="py-12 text-center text-xs text-slate-500">
                  No documents ingested yet. Click &quot;Ingest Source URL&quot; to fetch and archive external articles.
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Register Source Modal */}
      <Modal
        isOpen={isCreateSourceOpen}
        onClose={() => setIsCreateSourceOpen(false)}
        title="Register Curated Feed / Source"
        subtitle="Add a new regional news publisher, official portal, or OSINT sensor provider"
        maxWidth="md"
      >
        <form onSubmit={handleCreateSource} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Source Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Tehran Times or Reuters Middle East"
              value={createSourceForm.name}
              onChange={(e) => setCreateSourceForm({ ...createSourceForm, name: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Source Type</label>
              <select
                value={createSourceForm.source_type}
                onChange={(e) =>
                  setCreateSourceForm({ ...createSourceForm, source_type: e.target.value as SourceType })
                }
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="news_outlet">News Outlet</option>
                <option value="state_media">State Media</option>
                <option value="government">Government / Ministry</option>
                <option value="think_tank">Think Tank / Research</option>
                <option value="satellite">Satellite / Sensor Stream</option>
                <option value="telegram">Telegram Broadcast</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Default Language</label>
              <input
                type="text"
                placeholder="en, ar, fa, he"
                value={createSourceForm.default_language || "en"}
                onChange={(e) =>
                  setCreateSourceForm({ ...createSourceForm, default_language: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Base Homepage URL</label>
            <input
              type="url"
              placeholder="https://www.tehrantimes.com"
              value={createSourceForm.base_url || ""}
              onChange={(e) => setCreateSourceForm({ ...createSourceForm, base_url: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsCreateSourceOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isCreatingSource}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition"
            >
              {isCreatingSource ? "Saving..." : "Register Source"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Source Modal */}
      {editingSource && (
        <Modal
          isOpen={!!editingSource}
          onClose={() => setEditingSource(null)}
          title={`Edit Source: ${editingSource.name}`}
          subtitle="Modify feed classification, homepage, and operational status"
          maxWidth="md"
        >
          <form onSubmit={handleUpdateSource} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Source Name</label>
              <input
                type="text"
                required
                value={editSourceForm.name || ""}
                onChange={(e) => setEditSourceForm({ ...editSourceForm, name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Source Type</label>
                <select
                  value={editSourceForm.source_type || editingSource.source_type}
                  onChange={(e) =>
                    setEditSourceForm({ ...editSourceForm, source_type: e.target.value as SourceType })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="news_outlet">News Outlet</option>
                  <option value="state_media">State Media</option>
                  <option value="government">Government</option>
                  <option value="think_tank">Think Tank</option>
                  <option value="satellite">Satellite / Sensor</option>
                  <option value="telegram">Telegram Broadcast</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Language</label>
                <input
                  type="text"
                  value={editSourceForm.default_language || ""}
                  onChange={(e) =>
                    setEditSourceForm({ ...editSourceForm, default_language: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Base URL</label>
              <input
                type="url"
                value={editSourceForm.base_url || ""}
                onChange={(e) => setEditSourceForm({ ...editSourceForm, base_url: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="edit_src_enabled"
                checked={editSourceForm.enabled ?? true}
                onChange={(e) => setEditSourceForm({ ...editSourceForm, enabled: e.target.checked })}
                className="rounded bg-slate-950 border-slate-800 text-sky-600 focus:ring-0"
              />
              <label htmlFor="edit_src_enabled" className="text-xs text-slate-200">
                Active for automatic collector polling
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setEditingSource(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isUpdatingSource}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition"
              >
                {isUpdatingSource ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Add Endpoint Modal */}
      {endpointSourceId && (
        <Modal
          isOpen={!!endpointSourceId}
          onClose={() => setEndpointSourceId(null)}
          title="Add Collection Endpoint"
          subtitle="Configure an RSS feed URL, Web Scraper entrypoint, or API feed"
          maxWidth="md"
        >
          <form onSubmit={handleAddEndpoint} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Endpoint URL</label>
              <input
                type="url"
                required
                placeholder="https://www.aljazeera.com/xml/rss/all.xml"
                value={endpointForm.url}
                onChange={(e) => setEndpointForm({ ...endpointForm, url: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Endpoint Type</label>
                <select
                  value={endpointForm.endpoint_type}
                  onChange={(e) =>
                    setEndpointForm({ ...endpointForm, endpoint_type: e.target.value as EndpointType })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="rss">RSS / Atom Feed</option>
                  <option value="scraper">Web Scraper / HTML</option>
                  <option value="api">REST / JSON API</option>
                  <option value="telegram">Telegram Channel</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Polling Schedule Tier</label>
                <select
                  value={endpointForm.schedule || "critical"}
                  onChange={(e) => setEndpointForm({ ...endpointForm, schedule: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  <option value="critical">Critical (Every 10 min)</option>
                  <option value="normal">Normal (Hourly)</option>
                  <option value="daily">Daily (Every 24 hours)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setEndpointSourceId(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isAddingEndpoint}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition"
              >
                {isAddingEndpoint ? "Saving..." : "Add Endpoint"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Ingest Source URL Modal */}
      <Modal
        isOpen={isSubmitOpen}
        onClose={() => setIsSubmitOpen(false)}
        title="Ingest External Intelligence URL"
        subtitle="Fetches the webpage, cleans HTML boilerplate, detects language, and chunks content for LLM extraction"
        maxWidth="md"
      >
        <div className="space-y-4">
          <form onSubmit={handleSubmitSource} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Target Article URL</label>
              <input
                type="url"
                required
                placeholder="https://www.reuters.com/world/middle-east/..."
                value={submitForm.url}
                onChange={(e) => setSubmitForm({ ...submitForm, url: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Custom Title (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Official Statement on Bab el-Mandeb Transit Protocol"
                value={submitForm.title || ""}
                onChange={(e) => setSubmitForm({ ...submitForm, title: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsSubmitOpen(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition flex items-center gap-1.5"
              >
                {isSubmitting ? (
                  <>
                    <ActivityIcon className="w-3.5 h-3.5 animate-spin" /> Ingesting...
                  </>
                ) : (
                  "Ingest & Extract"
                )}
              </button>
            </div>
          </form>

          {/* Submission Preview Result */}
          {submitResult && (
            <div className="p-4 bg-emerald-950/20 border border-emerald-800/40 rounded-xl space-y-2 text-xs">
              <div className="flex items-center gap-2 text-emerald-300 font-semibold">
                <CheckCircleIcon className="w-4 h-4 text-emerald-400" />
                Document Successfully Ingested
              </div>
              <p className="text-slate-300 font-mono text-[11px]">
                Document ID: {submitResult.document_id}
              </p>
              {submitResult.extracted_text_preview && (
                <div className="p-2.5 bg-slate-950 rounded border border-slate-800 text-slate-300 text-[11px] leading-relaxed">
                  <span className="font-bold text-slate-500 uppercase block mb-1">Extracted Text Preview:</span>
                  {submitResult.extracted_text_preview}...
                </div>
              )}
            </div>
          )}
        </div>
      </Modal>

      {/* Selected Document Modal */}
      {selectedDocument && (
        <Modal
          isOpen={!!selectedDocument}
          onClose={() => setSelectedDocument(null)}
          title={selectedDocument.title || selectedDocument.canonical_url}
          subtitle={`Status: ${selectedDocument.status} • Chunks: ${selectedDocument.chunks.length}`}
          maxWidth="2xl"
        >
          <div className="space-y-4">
            <div className="text-xs text-slate-400 font-mono break-all">
              URL: {selectedDocument.canonical_url}
            </div>

            {selectedDocument.extracted_text && (
              <div>
                <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono mb-1">
                  Extracted Normalized Text
                </h5>
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-200 max-h-60 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                  {selectedDocument.extracted_text}
                </div>
              </div>
            )}

            {selectedDocument.chunks.length > 0 && (
              <div>
                <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono mb-2">
                  Document Chunks for Vector Embedding
                </h5>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {selectedDocument.chunks.map((chunk) => (
                    <div key={chunk.id} className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1">
                      <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                        <span>Chunk #{chunk.sequence}</span>
                        <span>{chunk.token_count ? `${chunk.token_count} tokens` : ""}</span>
                      </div>
                      <p className="text-slate-300 font-mono text-[11px]">{chunk.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import {
  Source,
  Document,
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

  // Submit Source Modal
  const [isSubmitOpen, setIsSubmitOpen] = useState(false);
  const [submitForm, setSubmitForm] = useState<SubmitSourceRequest>({
    url: "",
    title: "",
  });
  const [submitResult, setSubmitResult] = useState<SubmitSourceResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchData}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCwIcon className="w-4 h-4" />
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

            <div className="space-y-2 max-h-[440px] overflow-y-auto pr-1">
              {sources.map((s) => (
                <div
                  key={s.id}
                  className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg space-y-1 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{s.name}</span>
                    <Badge variant={s.enabled ? "success" : "neutral"} size="sm">
                      {s.source_type}
                    </Badge>
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

            <div className="space-y-3 max-h-[440px] overflow-y-auto pr-1">
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

      {/* Submit Source URL Modal */}
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

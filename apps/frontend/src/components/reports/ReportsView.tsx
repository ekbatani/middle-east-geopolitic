"use client";

import React, { useState, useEffect } from "react";
import {
  Report,
  ReportSummary,
  ReportType,
  ReportStatus,
  GenerateReportRequest,
  UpdateReportRequest,
  ScopeType,
} from "../../types";
import { reportsService } from "../../services";
import {
  FileTextIcon,
  PlusIcon,
  ActivityIcon,
  RefreshCwIcon,
  CheckCircleIcon,
  GlobeIcon,
  SparklesIcon,
  Trash2Icon,
} from "../common/Icons";
import { Card } from "../common/Card";
import { Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function ReportsView() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingReport, setLoadingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedType, setSelectedType] = useState<ReportType | undefined>(undefined);

  // Generate Report Modal
  const [isGenerateOpen, setIsGenerateOpen] = useState(false);
  const [generateForm, setGenerateForm] = useState<GenerateReportRequest>({
    report_type: "daily_brief",
    scope_type: "regional",
  });
  const [isGenerating, setIsGenerating] = useState(false);

  // Edit Report Modal
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editForm, setEditForm] = useState<UpdateReportRequest>({});
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchReports = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await reportsService.listReports({ report_type: selectedType });
      setReports(data);
    } catch (err) {
      console.error("Reports fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load reports");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [selectedType]);

  const handleSelectReport = async (summary: ReportSummary) => {
    setLoadingReport(true);
    try {
      const full = await reportsService.getReport(summary.id);
      setSelectedReport(full);
    } catch (err) {
      console.error("Report detail fetch error:", err);
    } finally {
      setLoadingReport(false);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    try {
      const generated = await reportsService.generateReport(generateForm);
      setIsGenerateOpen(false);
      setSelectedReport(generated);
      fetchReports();
    } catch (err) {
      console.error("Generate report error:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReport) return;

    setIsUpdating(true);
    try {
      const updated = await reportsService.updateReport(selectedReport.id, editForm);
      setIsEditOpen(false);
      setSelectedReport(updated);
      fetchReports();
    } catch (err) {
      console.error("Update report error:", err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDelete = async (reportId: string) => {
    if (!confirm("Are you sure you want to delete this report?")) return;
    try {
      await reportsService.deleteReport(reportId);
      if (selectedReport?.id === reportId) {
        setSelectedReport(null);
      }
      fetchReports();
    } catch (err) {
      console.error("Delete report error:", err);
    }
  };

  const handleApprove = async (reportId: string) => {
    try {
      const approved = await reportsService.approveReport(reportId);
      setSelectedReport(approved);
      fetchReports();
    } catch (err) {
      console.error("Approve report error:", err);
    }
  };

  const handlePublish = async (reportId: string) => {
    try {
      const published = await reportsService.publishReport(reportId);
      setSelectedReport(published);
      fetchReports();
    } catch (err) {
      console.error("Publish report error:", err);
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading intelligence briefings and analytical reports..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchReports} />;
  }

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <FileTextIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Executive Briefings & Intelligence Reports
            </h2>
            <p className="text-xs text-slate-400">
              Structured analytical assessments &bull; Multi-source narrative synthesis &bull; Formal approval & publication workflow
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <select
            value={selectedType || ""}
            onChange={(e) =>
              setSelectedType(e.target.value ? (e.target.value as ReportType) : undefined)
            }
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 cursor-pointer"
          >
            <option value="" className="bg-slate-900">All Report Types</option>
            <option value="daily_brief" className="bg-slate-900">Daily Brief</option>
            <option value="weekly_brief" className="bg-slate-900">Weekly Brief</option>
            <option value="country_brief" className="bg-slate-900">Country Brief</option>
            <option value="conflict_brief" className="bg-slate-900">Conflict Brief</option>
          </select>

          <button
            onClick={fetchReports}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCwIcon className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsGenerateOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            <PlusIcon className="w-4 h-4" />
            Generate Brief
          </button>
        </div>
      </div>

      {/* Reports Grid / Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Report List */}
        <div className="space-y-3 max-h-[calc(100vh-16rem)] overflow-y-auto pr-1">
          {reports.map((r) => {
            const isSelected = selectedReport?.id === r.id;
            return (
              <div
                key={r.id}
                onClick={() => handleSelectReport(r)}
                className={`p-4 rounded-xl border cursor-pointer transition space-y-2 ${
                  isSelected
                    ? "bg-slate-900 border-sky-500 shadow-md ring-1 ring-sky-500/20"
                    : "bg-slate-950/60 hover:bg-slate-900 border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between">
                  <Badge variant="info" size="sm">
                    {r.report_type.replace("_", " ")}
                  </Badge>
                  <div className="flex items-center gap-1.5">
                    <Badge
                      variant={
                        r.status === "published"
                          ? "success"
                          : r.status === "approved"
                          ? "info"
                          : "warning"
                      }
                      size="sm"
                    >
                      {r.status}
                    </Badge>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(r.id);
                      }}
                      className="text-slate-500 hover:text-rose-400 p-1"
                      title="Delete report"
                    >
                      <Trash2Icon className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <h4 className="text-xs font-bold text-slate-100 line-clamp-2">{r.title}</h4>

                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono pt-1">
                  <span>
                    {r.period_start ? `${r.period_start} → ${r.period_end || "Now"}` : "Ad-hoc"}
                  </span>
                  <span>{r.published_at ? new Date(r.published_at).toLocaleDateString() : "Draft"}</span>
                </div>
              </div>
            );
          })}

          {reports.length === 0 && (
            <div className="py-12 text-center text-xs text-slate-500">
              No reports found. Click &quot;Generate Brief&quot; to synthesize an intelligence report.
            </div>
          )}
        </div>

        {/* Right 2 Columns: Full Report Reader / Actions */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="h-full flex flex-col justify-between">
            {loadingReport ? (
              <LoadingState message="Loading formatted report document..." />
            ) : selectedReport ? (
              <div className="space-y-5">
                {/* Report Header & Action Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="info">{selectedReport.report_type.replace("_", " ")}</Badge>
                      <Badge
                        variant={
                          selectedReport.status === "published"
                            ? "success"
                            : selectedReport.status === "approved"
                            ? "info"
                            : "warning"
                        }
                      >
                        {selectedReport.status}
                      </Badge>
                    </div>
                    <h3 className="text-base font-bold text-slate-100">{selectedReport.title}</h3>
                  </div>

                  {/* Workflow Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        setEditForm({
                          title: selectedReport.title,
                          content_markdown: selectedReport.content_markdown,
                          status: selectedReport.status,
                        });
                        setIsEditOpen(true);
                      }}
                      className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
                    >
                      Edit Content
                    </button>

                    {selectedReport.status === "draft" && (
                      <button
                        onClick={() => handleApprove(selectedReport.id)}
                        className="px-3 py-1.5 bg-emerald-950 hover:bg-emerald-900 border border-emerald-800 text-emerald-200 text-xs font-semibold rounded-lg transition flex items-center gap-1"
                      >
                        <CheckCircleIcon className="w-3.5 h-3.5 text-emerald-400" />
                        Approve
                      </button>
                    )}
                    {selectedReport.status === "approved" && (
                      <button
                        onClick={() => handlePublish(selectedReport.id)}
                        className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow transition flex items-center gap-1"
                      >
                        <GlobeIcon className="w-3.5 h-3.5" />
                        Publish
                      </button>
                    )}
                  </div>
                </div>

                {/* Metadata tags */}
                <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-400 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  {selectedReport.generated_by_model && (
                    <span>Model: {selectedReport.generated_by_model}</span>
                  )}
                  {selectedReport.approved_by && (
                    <span>Approved By: {selectedReport.approved_by.slice(0, 8)}</span>
                  )}
                  {selectedReport.published_at && (
                    <span>Published: {new Date(selectedReport.published_at).toLocaleString()}</span>
                  )}
                </div>

                {/* Markdown Content */}
                <div className="bg-slate-950 p-5 rounded-xl border border-slate-800 text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-wrap max-h-[480px] overflow-y-auto custom-scrollbar">
                  {selectedReport.content_markdown}
                </div>
              </div>
            ) : (
              <div className="py-24 text-center text-slate-500 text-xs flex flex-col items-center justify-center">
                <FileTextIcon className="w-8 h-8 text-slate-600 mb-2" />
                Select a report from the list on the left to inspect full intelligence narrative.
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Generate Report Modal */}
      <Modal
        isOpen={isGenerateOpen}
        onClose={() => setIsGenerateOpen(false)}
        title="Generate Intelligence Briefing"
        subtitle="Initiates AI narrative synthesis over verified events and calibrated risk indicators"
        maxWidth="md"
      >
        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Report Type</label>
            <select
              value={generateForm.report_type}
              onChange={(e) =>
                setGenerateForm({ ...generateForm, report_type: e.target.value as ReportType })
              }
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="daily_brief">Daily Intelligence Brief</option>
              <option value="weekly_brief">Weekly Strategic Assessment</option>
              <option value="country_brief">Country-Specific Brief</option>
              <option value="conflict_brief">Conflict / Crisis Brief</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Scope</label>
            <select
              value={generateForm.scope_type || "regional"}
              onChange={(e) =>
                setGenerateForm({ ...generateForm, scope_type: e.target.value as ScopeType })
              }
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="regional">Regional Middle East</option>
              <option value="country">Country Focus</option>
              <option value="global">Global Implications</option>
            </select>
          </div>

          <p className="text-[11px] text-slate-400 bg-slate-950 p-3 rounded-lg border border-slate-800 leading-relaxed">
            The Report Generator pulls current observations, verified claims, and active indicators to draft executive summaries, key trends, and tactical outlooks.
          </p>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsGenerateOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isGenerating}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition flex items-center gap-1.5"
            >
              {isGenerating ? (
                <>
                  <ActivityIcon className="w-3.5 h-3.5 animate-spin" /> Synthesizing...
                </>
              ) : (
                <>
                  <SparklesIcon className="w-3.5 h-3.5" /> Generate Report
                </>
              )}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Report Modal */}
      {selectedReport && (
        <Modal
          isOpen={isEditOpen}
          onClose={() => setIsEditOpen(false)}
          title="Edit Intelligence Report"
          subtitle={`Report #${selectedReport.id.slice(0, 8)}`}
          maxWidth="lg"
        >
          <form onSubmit={handleUpdate} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Report Title</label>
              <input
                type="text"
                required
                value={editForm.title || ""}
                onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Status</label>
              <select
                value={editForm.status || selectedReport.status}
                onChange={(e) => setEditForm({ ...editForm, status: e.target.value as ReportStatus })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="draft">Draft</option>
                <option value="under_review">Under Review</option>
                <option value="approved">Approved</option>
                <option value="published">Published</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Markdown Content</label>
              <textarea
                rows={10}
                required
                value={editForm.content_markdown || ""}
                onChange={(e) => setEditForm({ ...editForm, content_markdown: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500 font-mono leading-relaxed"
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
    </div>
  );
}

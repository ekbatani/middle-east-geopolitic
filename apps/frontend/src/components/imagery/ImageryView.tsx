"use client";

import React, { useState, useEffect } from "react";
import { ImageEvidence, SubmitImageRequest, UpdateImageRequest, VerificationStatus } from "../../types";
import { imageryService } from "../../services";
import {
  SatelliteIcon,
  PlusIcon,
  RefreshCwIcon,
  SparklesIcon,
  Trash2Icon,
} from "../common/Icons";
import { Card } from "../common/Card";
import { Badge, VerificationBadge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function ImageryView() {
  const [images, setImages] = useState<ImageEvidence[]>([]);
  const [selectedImage, setSelectedImage] = useState<ImageEvidence | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Submit Image Modal
  const [isSubmitOpen, setIsSubmitOpen] = useState(false);
  const [submitForm, setSubmitForm] = useState<SubmitImageRequest>({
    image_url: "",
    caption: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isReanalyzing, setIsReanalyzing] = useState(false);

  // Edit Image Modal
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editForm, setEditForm] = useState<UpdateImageRequest>({});
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchImages = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await imageryService.listImages({ limit: 50 });
      setImages(data);
    } catch (err) {
      console.error("Imagery fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load imagery evidence");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
  }, []);

  const handleSubmitImage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!submitForm.image_url.trim()) return;

    setIsSubmitting(true);
    try {
      const created = await imageryService.submitImage(submitForm);
      setIsSubmitOpen(false);
      setSubmitForm({ image_url: "", caption: "" });
      fetchImages();
      setSelectedImage(created);
    } catch (err) {
      console.error("Submit image error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateImage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedImage) return;

    setIsUpdating(true);
    try {
      const updated = await imageryService.updateImage(selectedImage.id, editForm);
      setIsEditOpen(false);
      setSelectedImage(updated);
      fetchImages();
    } catch (err) {
      console.error("Update image error:", err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteImage = async (imageId: string) => {
    if (!confirm("Are you sure you want to delete this satellite imagery record?")) return;
    try {
      await imageryService.deleteImage(imageId);
      if (selectedImage?.id === imageId) {
        setSelectedImage(null);
      }
      fetchImages();
    } catch (err) {
      console.error("Delete image error:", err);
    }
  };

  const handleReanalyze = async (imageId: string) => {
    setIsReanalyzing(true);
    try {
      const updated = await imageryService.reanalyzeImage(imageId);
      setSelectedImage(updated);
      fetchImages();
    } catch (err) {
      console.error("Reanalyze error:", err);
    } finally {
      setIsReanalyzing(false);
    }
  };

  if (isLoading && images.length === 0) {
    return <LoadingState message="Loading satellite intelligence and open-source imagery evidence..." />;
  }

  if (error && images.length === 0) {
    return <ErrorState message={error} onRetry={fetchImages} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <SatelliteIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Satellite & Tactical Imagery Evidence
            </h2>
            <p className="text-xs text-slate-400">
              Commercial SAR/Electro-Optical imagery &bull; Bounding box object detection &bull; Geotagged corroboration
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchImages}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCwIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsSubmitOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            <PlusIcon className="w-4 h-4" />
            Ingest Imagery
          </button>
        </div>
      </div>

      {/* Grid Layout: Imagery Gallery & Inspector */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {images.map((img) => (
          <Card
            key={img.id}
            onClick={() => setSelectedImage(img)}
            className="flex flex-col justify-between p-4 bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition cursor-pointer space-y-3"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <VerificationBadge status={img.verification_status} />
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-mono text-slate-500">
                    {img.content_type}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteImage(img.id);
                    }}
                    className="text-slate-500 hover:text-rose-400 p-1"
                    title="Delete image"
                  >
                    <Trash2Icon className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Thumbnail Placeholder with radar crosshairs */}
              <div className="w-full aspect-video bg-slate-900 rounded-lg border border-slate-800 overflow-hidden relative flex items-center justify-center">
                <SatelliteIcon className="w-8 h-8 text-slate-700" />
                <span className="absolute bottom-2 right-2 text-[10px] font-mono text-slate-400 bg-slate-950/80 px-1.5 py-0.5 rounded">
                  {img.latitude && img.longitude
                    ? `${img.latitude.toFixed(2)}°N, ${img.longitude.toFixed(2)}°E`
                    : "No Geotag"}
                </span>
              </div>

              <h4 className="text-xs font-semibold text-slate-200 line-clamp-2 mt-2">
                {img.caption || `Imagery Artifact #${img.id.slice(0, 8)}`}
              </h4>
            </div>

            <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 font-mono flex items-center justify-between">
              <span>Retrieved: {new Date(img.retrieved_at).toLocaleDateString()}</span>
              <span>Conf: {img.confidence ? `${Math.round(img.confidence * 100)}%` : "N/A"}</span>
            </div>
          </Card>
        ))}

        {images.length === 0 && (
          <div className="col-span-full py-16 text-center text-xs text-slate-500 bg-slate-950 rounded-2xl border border-slate-800">
            No satellite or tactical imagery artifacts submitted yet. Click &quot;Ingest Imagery&quot; to register image evidence.
          </div>
        )}
      </div>

      {/* Image Inspection Modal */}
      {selectedImage && (
        <Modal
          isOpen={!!selectedImage}
          onClose={() => setSelectedImage(null)}
          title={selectedImage.caption || `Imagery Evidence: ${selectedImage.id.slice(0, 8)}`}
          subtitle={`Hash: ${selectedImage.content_hash.slice(0, 16)}... • Type: ${selectedImage.content_type}`}
          maxWidth="2xl"
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <VerificationBadge status={selectedImage.verification_status} />
                {selectedImage.latitude && selectedImage.longitude && (
                  <Badge variant="info">
                    📍 {selectedImage.latitude.toFixed(4)}°N, {selectedImage.longitude.toFixed(4)}°E
                  </Badge>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setEditForm({
                      caption: selectedImage.caption,
                      latitude: selectedImage.latitude,
                      longitude: selectedImage.longitude,
                      verification_status: selectedImage.verification_status,
                    });
                    setIsEditOpen(true);
                  }}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
                >
                  Edit Metadata
                </button>
                <button
                  onClick={() => handleReanalyze(selectedImage.id)}
                  disabled={isReanalyzing}
                  className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium rounded-lg transition flex items-center gap-1.5"
                >
                  <SparklesIcon className="w-3.5 h-3.5 text-white" />
                  {isReanalyzing ? "Re-analyzing..." : "Run AI Vision"}
                </button>
              </div>
            </div>

            {/* Simulated Imagery Inspector Frame */}
            <div className="w-full aspect-video bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-center relative overflow-hidden">
              <div className="text-center space-y-2">
                <SatelliteIcon className="w-12 h-12 text-slate-700 mx-auto" />
                <p className="text-xs text-slate-400 font-mono">
                  MINIO OBJECT KEY: {selectedImage.id}
                </p>
              </div>

              {/* Overlay Crosshairs */}
              <div className="absolute inset-0 border border-sky-500/20 pointer-events-none grid grid-cols-3 grid-rows-3" />
            </div>

            {/* Analysis JSON Output */}
            {selectedImage.analysis && Object.keys(selectedImage.analysis).length > 0 && (
              <div>
                <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono mb-1">
                  Computer Vision & Object Detection Annotations:
                </h5>
                <pre className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-[11px] font-mono text-slate-300 max-h-40 overflow-y-auto">
                  {JSON.stringify(selectedImage.analysis, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Edit Image Modal */}
      {selectedImage && (
        <Modal
          isOpen={isEditOpen}
          onClose={() => setIsEditOpen(false)}
          title="Edit Imagery Metadata"
          subtitle={`Update caption, geospatial geotag coordinates, and verification state`}
          maxWidth="md"
        >
          <form onSubmit={handleUpdateImage} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Caption</label>
              <input
                type="text"
                value={editForm.caption || ""}
                onChange={(e) => setEditForm({ ...editForm, caption: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={editForm.latitude ?? ""}
                  onChange={(e) =>
                    setEditForm({ ...editForm, latitude: e.target.value ? Number(e.target.value) : undefined })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={editForm.longitude ?? ""}
                  onChange={(e) =>
                    setEditForm({ ...editForm, longitude: e.target.value ? Number(e.target.value) : undefined })
                  }
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Verification Status</label>
              <select
                value={editForm.verification_status || selectedImage.verification_status}
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

      {/* Submit Image Modal */}
      <Modal
        isOpen={isSubmitOpen}
        onClose={() => setIsSubmitOpen(false)}
        title="Ingest Satellite or OSINT Imagery"
        subtitle="Submit image artifact URL for automated object detection and evidence bundle linking"
        maxWidth="md"
      >
        <form onSubmit={handleSubmitImage} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Image URL</label>
            <input
              type="url"
              required
              placeholder="https://satellite.source.org/passes/2026/hormuz_ir_01.jpg"
              value={submitForm.image_url}
              onChange={(e) => setSubmitForm({ ...submitForm, image_url: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono focus:outline-none focus:border-sky-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Caption / Subject</label>
            <input
              type="text"
              placeholder="e.g. High-resolution SAR pass showing missile fast-attack craft deployment"
              value={submitForm.caption || ""}
              onChange={(e) => setSubmitForm({ ...submitForm, caption: e.target.value })}
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
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition"
            >
              {isSubmitting ? "Ingesting..." : "Ingest Image"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

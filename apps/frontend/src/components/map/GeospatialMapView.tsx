"use client";

import React, { useState, useEffect, useMemo } from "react";
import { MapEvent, CreateEventRequest } from "../../types";
import { intelligenceService, eventsService } from "../../services";
import {
  CompassIcon,
  FilterIcon,
  RefreshCwIcon,
  PlusIcon,
  ActivityIcon,
  MapPinIcon,
  CheckCircleIcon,
  XCircleIcon,
} from "../common/Icons";
import { Card, CardHeader } from "../common/Card";
import { SeverityBadge, VerificationBadge, Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

// Middle East Bounding Box: Lon [25, 65], Lat [12, 42]
const BBOX = {
  minLon: 25,
  maxLon: 65,
  minLat: 12,
  maxLat: 42,
};

function projectCoords(lon: number, lat: number, width: number, height: number) {
  const x = ((lon - BBOX.minLon) / (BBOX.maxLon - BBOX.minLon)) * width;
  // Invert Y because SVG coordinates have Y=0 at top
  const y = (1 - (lat - BBOX.minLat) / (BBOX.maxLat - BBOX.minLat)) * height;
  return { x, y };
}

export function GeospatialMapView() {
  const [mapEvents, setMapEvents] = useState<MapEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [minSeverity, setMinSeverity] = useState<number | undefined>(undefined);
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("");
  const [selectedEvent, setSelectedEvent] = useState<MapEvent | null>(null);

  // Create Event Modal
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState<CreateEventRequest>({
    title: "",
    event_type: "kinetic_strike",
    started_at: new Date().toISOString().slice(0, 16),
    severity: 3,
    summary: "",
    strategic_significance: "",
  });
  const [locName, setLocName] = useState("");
  const [locLat, setLocLat] = useState<number>(33.5);
  const [locLon, setLocLon] = useState<number>(36.3);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchMapEvents = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await intelligenceService.getMapEvents({
        min_severity: minSeverity,
        event_type: eventTypeFilter || undefined,
        limit: 200,
      });
      setMapEvents(data);
    } catch (err) {
      console.error("Map events fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load map events");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMapEvents();
  }, [minSeverity, eventTypeFilter]);

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const created = await eventsService.createEvent({
        ...createForm,
        started_at: new Date(createForm.started_at).toISOString(),
      });
      if (locName.trim() && locLat && locLon) {
        await eventsService.addLocation(created.id, {
          name: locName.trim(),
          latitude: Number(locLat),
          longitude: Number(locLon),
        });
      }
      setIsCreateModalOpen(false);
      setCreateForm({
        title: "",
        event_type: "kinetic_strike",
        started_at: new Date().toISOString().slice(0, 16),
        severity: 3,
        summary: "",
        strategic_significance: "",
      });
      fetchMapEvents();
    } catch (err) {
      console.error("Create event error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApproveEvent = async (eventId: string) => {
    try {
      await eventsService.approveEvent(eventId);
      fetchMapEvents();
      if (selectedEvent && selectedEvent.event_id === eventId) {
        setSelectedEvent((prev) => (prev ? { ...prev, verification_status: "confirmed" } : null));
      }
    } catch (err) {
      console.error("Approve error:", err);
    }
  };

  const handleRejectEvent = async (eventId: string) => {
    try {
      await eventsService.rejectEvent(eventId);
      fetchMapEvents();
      if (selectedEvent && selectedEvent.event_id === eventId) {
        setSelectedEvent(null);
      }
    } catch (err) {
      console.error("Reject error:", err);
    }
  };

  // SVG dimensions
  const svgWidth = 800;
  const svgHeight = 500;

  // Major theater anchor points for background reference grid
  const referenceTheaters = useMemo(
    () => [
      { name: "Levant / Damascus", lon: 36.3, lat: 33.5 },
      { name: "Tehran / Persian Gulf", lon: 51.4, lat: 35.7 },
      { name: "Baghdad / Tigris", lon: 44.4, lat: 33.3 },
      { name: "Riyadh / Gulf Coast", lon: 46.7, lat: 24.7 },
      { name: "Strait of Hormuz", lon: 56.4, lat: 26.6 },
      { name: "Bab el-Mandeb / Red Sea", lon: 43.3, lat: 12.6 },
      { name: "Suez / Sinai", lon: 32.5, lat: 29.9 },
      { name: "Ankara / Anatolia", lon: 32.8, lat: 39.9 },
      { name: "Beirut / Litani", lon: 35.5, lat: 33.9 },
      { name: "Tel Aviv / Gaza", lon: 34.8, lat: 31.8 },
      { name: "Sanaa / Hodeidah", lon: 44.2, lat: 15.3 },
    ],
    []
  );

  return (
    <div className="space-y-6">
      {/* Top Header & Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <CompassIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Geospatial Theater & Kinetic Intel Map
            </h2>
            <p className="text-xs text-slate-400">
              Bounding Box: 25°E–65°E, 12°N–42°N &bull; Spatial incident clustering & tactical hotspot monitoring
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Severity filter */}
          <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1.5 rounded-lg border border-slate-800 text-xs">
            <FilterIcon className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Min Severity:</span>
            <select
              value={minSeverity ?? ""}
              onChange={(e) =>
                setMinSeverity(e.target.value ? Number(e.target.value) : undefined)
              }
              className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer"
            >
              <option value="" className="bg-slate-900">All</option>
              <option value="1" className="bg-slate-900">1+ (Low)</option>
              <option value="2" className="bg-slate-900">2+ (Moderate)</option>
              <option value="3" className="bg-slate-900">3+ (Elevated)</option>
              <option value="4" className="bg-slate-900">4+ (High)</option>
              <option value="5" className="bg-slate-900">5 (Critical)</option>
            </select>
          </div>

          {/* Event type filter */}
          <input
            type="text"
            placeholder="Filter event type..."
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 w-36"
          />

          <button
            onClick={fetchMapEvents}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCwIcon className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            <PlusIcon className="w-4 h-4" />
            New Event
          </button>
        </div>
      </div>

      {/* Main Map Viewport & Side Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Interactive Map Canvas */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-0 overflow-hidden bg-slate-950 border border-slate-800">
            <div className="relative w-full aspect-[16/10] bg-[#090d16] overflow-hidden flex items-center justify-center">
              {isLoading ? (
                <LoadingState message="Plotting kinetic incident coordinates..." />
              ) : error ? (
                <ErrorState message={error} onRetry={fetchMapEvents} />
              ) : (
                <svg
                  viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                  className="w-full h-full select-none cursor-crosshair"
                >
                  {/* Subtle Grid Lines (Lat/Lon) */}
                  <defs>
                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.5" />
                    </pattern>
                    {/* Glowing marker filters */}
                    <radialGradient id="crit-glow" cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.8" />
                      <stop offset="100%" stopColor="#f43f5e" stopOpacity="0" />
                    </radialGradient>
                    <radialGradient id="warn-glow" cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.8" />
                      <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
                    </radialGradient>
                  </defs>

                  <rect width={svgWidth} height={svgHeight} fill="url(#grid)" />

                  {/* Regional Outline Simulation / Tactical Sectors */}
                  <path
                    d="M 120 180 Q 200 120, 350 140 T 600 160 T 720 300 Q 600 420, 380 400 T 160 320 Z"
                    fill="none"
                    stroke="#1e293b"
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                  />

                  {/* Maritime Chokepoint Corridors */}
                  {/* Strait of Hormuz */}
                  <line x1="580" y1="240" x2="660" y2="280" stroke="#0284c7" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
                  {/* Bab el-Mandeb */}
                  <line x1="330" y1="460" x2="410" y2="440" stroke="#0284c7" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
                  {/* Suez */}
                  <line x1="140" y1="200" x2="160" y2="240" stroke="#0284c7" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />

                  {/* Theater Base Reference Markers */}
                  {referenceTheaters.map((t) => {
                    const { x, y } = projectCoords(t.lon, t.lat, svgWidth, svgHeight);
                    return (
                      <g key={t.name} transform={`translate(${x}, ${y})`}>
                        <circle r="2" fill="#475569" />
                        <text
                          x="5"
                          y="3"
                          fill="#64748b"
                          fontSize="9"
                          fontFamily="monospace"
                          className="pointer-events-none"
                        >
                          {t.name}
                        </text>
                      </g>
                    );
                  })}

                  {/* Kinetic Event Markers plotted on coordinates */}
                  {mapEvents.map((evt) => {
                    return evt.locations.map((loc) => {
                      if (loc.longitude === null || loc.latitude === null || loc.longitude === undefined || loc.latitude === undefined)
                        return null;

                      const { x, y } = projectCoords(loc.longitude, loc.latitude, svgWidth, svgHeight);
                      const isSelected = selectedEvent?.event_id === evt.event_id;
                      const severity = evt.severity || 1;
                      const isCritical = severity >= 4;

                      return (
                        <g
                          key={`${evt.event_id}-${loc.name}`}
                          transform={`translate(${x}, ${y})`}
                          onClick={() => setSelectedEvent(evt)}
                          className="cursor-pointer transition hover:opacity-100"
                        >
                          {/* Outer pulse circle */}
                          {isCritical && (
                            <circle
                              r="16"
                              fill="url(#crit-glow)"
                              className="animate-ping"
                              style={{ animationDuration: "3s" }}
                            />
                          )}

                          {/* Selection ring */}
                          {isSelected && (
                            <circle r="12" fill="none" stroke="#38bdf8" strokeWidth="2" strokeDasharray="2 2" />
                          )}

                          {/* Marker Core */}
                          <circle
                            r={isCritical ? "6" : "4.5"}
                            fill={
                              isCritical
                                ? "#f43f5e"
                                : severity === 3
                                ? "#f59e0b"
                                : "#0284c7"
                            }
                            stroke="#ffffff"
                            strokeWidth="1.5"
                          />

                          {/* Label tooltip */}
                          <text
                            x="8"
                            y="-4"
                            fill={isSelected ? "#38bdf8" : "#e2e8f0"}
                            fontSize="10"
                            fontWeight={isSelected ? "bold" : "normal"}
                            className="bg-slate-900 drop-shadow-md pointer-events-none"
                          >
                            {evt.title.length > 24 ? `${evt.title.slice(0, 24)}...` : evt.title}
                          </text>
                        </g>
                      );
                    });
                  })}
                </svg>
              )}

              {/* Map Legend Overlay */}
              <div className="absolute bottom-3 left-3 bg-slate-950/80 backdrop-blur-md border border-slate-800 rounded-lg p-2.5 text-[10px] space-y-1.5 font-mono text-slate-300">
                <div className="font-bold text-slate-400 uppercase tracking-wider mb-1">Severity Legend</div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
                  <span>Critical Incident (4–5)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  <span>Elevated Tension (3)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-500" />
                  <span>Standard Kinetic / Patrol (1–2)</span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Col: Selected Event Detail & Incident Feed */}
        <div className="space-y-4">
          <Card>
            <CardHeader
              title={selectedEvent ? "Incident Inspection" : "Spatial Incident Feed"}
              subtitle={
                selectedEvent
                  ? `Event ID: ${selectedEvent.event_id.slice(0, 8)}`
                  : `${mapEvents.length} incidents in current bounding box`
              }
              icon={<MapPinIcon className="w-5 h-5" />}
              action={
                selectedEvent && (
                  <button
                    onClick={() => setSelectedEvent(null)}
                    className="text-xs text-slate-400 hover:text-slate-200"
                  >
                    Clear selection
                  </button>
                )
              }
            />

            {selectedEvent ? (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <SeverityBadge severity={selectedEvent.severity} />
                    <VerificationBadge status={selectedEvent.verification_status} />
                  </div>
                  <h3 className="text-sm font-bold text-slate-100">{selectedEvent.title}</h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    TYPE: {selectedEvent.event_type} &bull; {new Date(selectedEvent.started_at).toLocaleString()}
                  </span>
                </div>

                {selectedEvent.strategic_significance && (
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                    <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono mb-1">
                      Strategic Significance
                    </h5>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {selectedEvent.strategic_significance}
                    </p>
                  </div>
                )}

                {/* Locations list */}
                <div>
                  <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono mb-1.5">
                    Targeted Locations
                  </h5>
                  <div className="space-y-1">
                    {selectedEvent.locations.map((loc, i) => (
                      <div
                        key={i}
                        className="p-2 bg-slate-950 rounded border border-slate-800 text-xs flex items-center justify-between"
                      >
                        <span className="text-slate-200 font-medium">{loc.name}</span>
                        {loc.latitude && loc.longitude && (
                          <span className="text-[10px] text-slate-400 font-mono">
                            {loc.latitude.toFixed(2)}°N, {loc.longitude.toFixed(2)}°E
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-2 flex items-center gap-2">
                  <button
                    onClick={() => handleApproveEvent(selectedEvent.event_id)}
                    className="flex-1 py-1.5 bg-emerald-950 hover:bg-emerald-900 border border-emerald-800 text-emerald-200 rounded-lg text-xs font-semibold transition flex items-center justify-center gap-1"
                  >
                    <CheckCircleIcon className="w-3.5 h-3.5 text-emerald-400" />
                    Approve Event
                  </button>
                  <button
                    onClick={() => handleRejectEvent(selectedEvent.event_id)}
                    className="flex-1 py-1.5 bg-rose-950 hover:bg-rose-900 border border-rose-800 text-rose-200 rounded-lg text-xs font-semibold transition flex items-center justify-center gap-1"
                  >
                    <XCircleIcon className="w-3.5 h-3.5 text-rose-400" />
                    Reject / Flag
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
                {mapEvents.length > 0 ? (
                  mapEvents.map((evt) => (
                    <div
                      key={evt.event_id}
                      onClick={() => setSelectedEvent(evt)}
                      className="p-2.5 bg-slate-950/60 hover:bg-slate-800/80 border border-slate-800 rounded-lg cursor-pointer transition space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <SeverityBadge severity={evt.severity} />
                        <span className="text-[10px] text-slate-500 font-mono">
                          {new Date(evt.started_at).toLocaleDateString()}
                        </span>
                      </div>
                      <h4 className="text-xs font-semibold text-slate-200 line-clamp-1">{evt.title}</h4>
                      {evt.locations.length > 0 && (
                        <span className="text-[10px] text-slate-400">
                          📍 {evt.locations.map((l) => l.name).join(", ")}
                        </span>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="py-8 text-center text-xs text-slate-500">
                    No kinetic incidents found matching filters.
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Create Event Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Record Kinetic / Geopolitical Event"
        subtitle="Log a verified development with geographical coordinates and strategic severity"
        maxWidth="lg"
      >
        <form onSubmit={handleCreateEvent} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Event Title</label>
            <input
              type="text"
              required
              placeholder="e.g., Drone Interception over Red Sea Corridor"
              value={createForm.title}
              onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Event Type</label>
              <select
                value={createForm.event_type}
                onChange={(e) => setCreateForm({ ...createForm, event_type: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="kinetic_strike">Kinetic Strike / Missile</option>
                <option value="maritime_interception">Maritime Interception</option>
                <option value="troop_movement">Troop Deployment</option>
                <option value="diplomatic_breakthrough">Diplomatic Statement</option>
                <option value="cyber_attack">Cyber Operation</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Severity (1–5)</label>
              <select
                value={createForm.severity || 3}
                onChange={(e) => setCreateForm({ ...createForm, severity: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="1">1 - Routine / Low</option>
                <option value="2">2 - Moderate</option>
                <option value="3">3 - Elevated Threat</option>
                <option value="4">4 - High Escalation</option>
                <option value="5">5 - Critical War Outbreak</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Location Name</label>
              <input
                type="text"
                placeholder="e.g. Strait of Hormuz"
                value={locName}
                onChange={(e) => setLocName(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Latitude (°N)</label>
              <input
                type="number"
                step="any"
                value={locLat}
                onChange={(e) => setLocLat(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Longitude (°E)</label>
              <input
                type="number"
                step="any"
                value={locLon}
                onChange={(e) => setLocLon(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Summary</label>
            <textarea
              rows={2}
              placeholder="Incident details, munitions identified, source corroboration..."
              value={createForm.summary || ""}
              onChange={(e) => setCreateForm({ ...createForm, summary: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsCreateModalOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-xs font-semibold text-white rounded-lg flex items-center gap-1.5"
            >
              {isSubmitting ? (
                <>
                  <ActivityIcon className="w-3.5 h-3.5 animate-spin" /> Recording...
                </>
              ) : (
                "Save Incident"
              )}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

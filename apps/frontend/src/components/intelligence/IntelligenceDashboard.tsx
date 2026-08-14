"use client";

import React, { useState, useEffect } from "react";
import {
  Event,
  RiskCatalogItem,
  Report,
  Actor,
  CountryBriefResponse,
} from "../../types";
import {
  eventsService,
  risksService,
  intelligenceService,
  actorsService,
} from "../../services";
import {
  ActivityIcon,
  ShieldIcon,
  SparklesIcon,
  GlobeIcon,
  RefreshCwIcon,
  CompassIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  FileTextIcon,
} from "../common/Icons";
import { Card, CardHeader } from "../common/Card";
import { Badge, SeverityBadge, VerificationBadge, TrendBadge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

type DashboardProps = {
  onNavigate: (section: string) => void;
};

export function IntelligenceDashboard({ onNavigate }: DashboardProps) {
  const [events, setEvents] = useState<Event[]>([]);
  const [risks, setRisks] = useState<RiskCatalogItem[]>([]);
  const [countries, setCountries] = useState<Actor[]>([]);
  const [dailyBrief, setDailyBrief] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Country Brief Modal State
  const [selectedCountry, setSelectedCountry] = useState<Actor | null>(null);
  const [countryBrief, setCountryBrief] = useState<CountryBriefResponse | null>(null);
  const [loadingBrief, setLoadingBrief] = useState(false);

  // Selected Event Details Modal
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [eventsData, risksData, actorsData] = await Promise.all([
        eventsService.listEvents({ limit: 8 }),
        risksService.listRisks(),
        actorsService.listActors({ actor_type: "country", limit: 20 }),
      ]);
      setEvents(eventsData);
      setRisks(risksData);
      setCountries(actorsData);
    } catch (err) {
      console.error("Dashboard data load error:", err);
      setError(err instanceof Error ? err.message : "Failed to load dashboard data");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenCountryBrief = async (country: Actor) => {
    setSelectedCountry(country);
    setLoadingBrief(true);
    try {
      const brief = await intelligenceService.getCountryBrief({ country_actor_id: country.id });
      setCountryBrief(brief);
    } catch (err) {
      console.error("Country brief error:", err);
    } finally {
      setLoadingBrief(false);
    }
  };

  const handleGenerateDailyBrief = async () => {
    try {
      const brief = await intelligenceService.getDailyBrief();
      setDailyBrief(brief);
    } catch (err) {
      console.error("Generate brief error:", err);
    }
  };

  if (isLoading) {
    return <LoadingState message="Aggregating Middle East geopolitical intelligence feeds..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-6">
      {/* Top Banner: Strategic Overview & Summary Stats */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="info">Theater Pulse</Badge>
              <span className="text-xs text-slate-400 font-mono">
                LAST UPDATED: {new Date().toLocaleTimeString()}
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-100">
              Middle East Strategic Intelligence & Risk Matrix
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Continuous multi-source monitoring of state actors, kinetic clashes, proxy networks, and maritime chokepoints across the Levant, Persian Gulf, and Red Sea.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchData}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
            >
              <RefreshCwIcon className="w-3.5 h-3.5" />
              Refresh Feeds
            </button>
            <button
              onClick={handleGenerateDailyBrief}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
            >
              <SparklesIcon className="w-3.5 h-3.5" />
              Generate Daily Brief
            </button>
          </div>
        </div>

        {/* Metric Cards Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5">
            <span className="text-[11px] font-mono text-slate-400 uppercase">Monitored Events</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-slate-100">{events.length}</span>
              <span className="text-xs text-emerald-400 font-medium">Active</span>
            </div>
          </div>
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5">
            <span className="text-[11px] font-mono text-slate-400 uppercase">Risk Domains</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-slate-100">{risks.length}</span>
              <span className="text-xs text-amber-400 font-medium">Calibrated</span>
            </div>
          </div>
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5">
            <span className="text-[11px] font-mono text-slate-400 uppercase">Key State Actors</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-slate-100">{countries.length}</span>
              <span className="text-xs text-sky-400 font-medium">Tracked</span>
            </div>
          </div>
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5">
            <span className="text-[11px] font-mono text-slate-400 uppercase">Alert Level</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-rose-400">ELEVATED</span>
              <span className="text-xs text-slate-400 font-mono">DEFCON 3</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Kinetic Events Feed & Risk Domains */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Breaking Verified Kinetic Events */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader
              title="Recent Kinetic Events & Intelligence Developments"
              subtitle="Verified geopolitical and military events ordered by temporal recency"
              icon={<ActivityIcon className="w-5 h-5" />}
              action={
                <button
                  onClick={() => onNavigate("map")}
                  className="text-xs text-sky-400 hover:text-sky-300 font-medium flex items-center gap-1"
                >
                  <CompassIcon className="w-3.5 h-3.5" />
                  View Geospatial Map &rarr;
                </button>
              }
            />

            <div className="space-y-3">
              {events.length > 0 ? (
                events.map((event) => (
                  <div
                    key={event.id}
                    onClick={() => setSelectedEvent(event)}
                    className="p-4 bg-slate-950/50 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 rounded-xl cursor-pointer transition space-y-2"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <SeverityBadge severity={event.severity} />
                          <VerificationBadge status={event.verification_status} />
                          <span className="text-xs text-slate-500 font-mono">
                            {new Date(event.started_at).toLocaleDateString()}
                          </span>
                        </div>
                        <h4 className="text-sm font-semibold text-slate-100 hover:text-sky-400 transition">
                          {event.title}
                        </h4>
                      </div>
                    </div>

                    {event.summary && (
                      <p className="text-xs text-slate-400 line-clamp-2">{event.summary}</p>
                    )}

                    {/* Locations & Actors tags */}
                    <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px] text-slate-400">
                      {event.locations.map((loc) => (
                        <span key={loc.id} className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                          📍 {loc.name}
                        </span>
                      ))}
                      {event.actors.map((act) => (
                        <span key={act.actor_id} className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-sky-300">
                          👤 {act.role}
                        </span>
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-xs text-slate-500">
                  No kinetic events recorded in database yet.
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right Col: Country Matrix & Strategic Risk Domains */}
        <div className="space-y-6">
          {/* Country Quick Access Matrix */}
          <Card>
            <CardHeader
              title="Country Intelligence Briefings"
              subtitle="Select a regional power for bilateral & risk deep dive"
              icon={<GlobeIcon className="w-5 h-5" />}
            />
            <div className="grid grid-cols-2 gap-2">
              {countries.slice(0, 10).map((c) => (
                <button
                  key={c.id}
                  onClick={() => handleOpenCountryBrief(c)}
                  className="p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800 border border-slate-800 hover:border-sky-500/50 text-left transition flex items-center justify-between"
                >
                  <span className="text-xs font-semibold text-slate-200 truncate">
                    {c.canonical_name}
                  </span>
                  <span className="text-[10px] text-sky-400 font-mono">&rarr;</span>
                </button>
              ))}
            </div>
          </Card>

          {/* Strategic Risk Engine Catalog */}
          <Card>
            <CardHeader
              title="Risk Engine Catalog"
              subtitle="Active risk categories & latest assessed scores"
              icon={<ShieldIcon className="w-5 h-5" />}
              action={
                <button
                  onClick={() => onNavigate("risks")}
                  className="text-xs text-sky-400 hover:text-sky-300 font-medium"
                >
                  Details &rarr;
                </button>
              }
            />

            <div className="space-y-2.5">
              {risks.slice(0, 6).map((item) => (
                <div
                  key={item.definition.id}
                  className="p-3 rounded-lg bg-slate-950/50 border border-slate-800/80 flex items-center justify-between gap-3"
                >
                  <div>
                    <h5 className="text-xs font-semibold text-slate-200">
                      {item.definition.name}
                    </h5>
                    <span className="text-[10px] text-slate-400 font-mono">
                      CODE: {item.definition.code}
                    </span>
                  </div>

                  <div className="text-right">
                    {item.latest_assessment ? (
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-bold text-slate-100 font-mono">
                          {item.latest_assessment.final_score}
                        </span>
                        <TrendBadge trend={item.latest_assessment.trend} />
                      </div>
                    ) : (
                      <span className="text-[11px] text-slate-500 font-mono">Unassessed</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Country Brief Modal */}
      {selectedCountry && (
        <Modal
          isOpen={!!selectedCountry}
          onClose={() => setSelectedCountry(null)}
          title={`Country Assessment: ${selectedCountry.canonical_name}`}
          subtitle="Unified intelligence assessment, active risk breakdown, and bilateral relationships"
          maxWidth="2xl"
        >
          {loadingBrief ? (
            <LoadingState message={`Generating country brief for ${selectedCountry.canonical_name}...`} />
          ) : countryBrief ? (
            <div className="space-y-5">
              {/* Risk Dimensions */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono mb-2.5">
                  Assessed Risk Dimensions
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {countryBrief.risks.map((r) => (
                    <div
                      key={r.risk_code}
                      className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-200">{r.risk_name}</span>
                        <span className="text-sm font-bold font-mono text-sky-400">
                          {r.dimension.score}/100
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 line-clamp-2">
                        {r.dimension.explanation || "No explanation recorded."}
                      </p>
                      <div className="flex items-center gap-2 pt-1">
                        <TrendBadge trend={r.dimension.trend} />
                        <span className="text-[10px] text-slate-500 font-mono">
                          Confidence: {Math.round(r.dimension.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bilateral Relationships */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono mb-2.5">
                  Bilateral Relationships & Escalation Risk
                </h4>
                <div className="space-y-2">
                  {countryBrief.relationships.map((rel) => (
                    <div
                      key={rel.relationship_id}
                      className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-semibold text-slate-200">{rel.counterpart_name}</span>
                        <span className="text-[10px] text-slate-500 ml-2 uppercase font-mono">
                          ({rel.relationship_type})
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-slate-400">Escalation Score:</span>
                        <span className="font-mono font-bold text-amber-400">
                          {rel.escalation_risk_score !== null ? rel.escalation_risk_score : "N/A"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-400 py-6 text-center">
              No country brief data found.
            </div>
          )}
        </Modal>
      )}

      {/* Event Details Modal */}
      {selectedEvent && (
        <Modal
          isOpen={!!selectedEvent}
          onClose={() => setSelectedEvent(null)}
          title={selectedEvent.title}
          subtitle={`Event Type: ${selectedEvent.event_type} • Started: ${new Date(selectedEvent.started_at).toLocaleString()}`}
          maxWidth="lg"
        >
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <SeverityBadge severity={selectedEvent.severity} />
              <VerificationBadge status={selectedEvent.verification_status} />
              <Badge variant="neutral">Status: {selectedEvent.lifecycle_status}</Badge>
            </div>

            {selectedEvent.summary && (
              <div>
                <h5 className="text-xs font-bold text-slate-400 uppercase font-mono mb-1">Summary</h5>
                <p className="text-xs text-slate-200 leading-relaxed bg-slate-950 p-3 rounded-lg border border-slate-800">
                  {selectedEvent.summary}
                </p>
              </div>
            )}

            {selectedEvent.strategic_significance && (
              <div>
                <h5 className="text-xs font-bold text-slate-400 uppercase font-mono mb-1">Strategic Significance</h5>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {selectedEvent.strategic_significance}
                </p>
              </div>
            )}

            {selectedEvent.impacts.length > 0 && (
              <div>
                <h5 className="text-xs font-bold text-slate-400 uppercase font-mono mb-1">Impacts & Magnitudes</h5>
                <div className="space-y-1.5">
                  {selectedEvent.impacts.map((imp) => (
                    <div key={imp.id} className="p-2 bg-slate-950 rounded border border-slate-800 text-xs flex justify-between">
                      <span className="text-slate-300 font-medium">{imp.impact_type}</span>
                      <span className="font-mono text-sky-400">
                        {imp.magnitude !== null ? `${imp.magnitude} ${imp.unit || ""}` : "Estimate recorded"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Daily Brief Generated Modal */}
      {dailyBrief && (
        <Modal
          isOpen={!!dailyBrief}
          onClose={() => setDailyBrief(null)}
          title={dailyBrief.title}
          subtitle={`Generated by: ${dailyBrief.generated_by_model || "Deterministic Engine"} • Status: ${dailyBrief.status}`}
          maxWidth="2xl"
        >
          <div className="space-y-4">
            <div className="prose prose-invert prose-xs max-w-none bg-slate-950 p-5 rounded-xl border border-slate-800 text-slate-300 whitespace-pre-wrap font-sans text-xs leading-relaxed">
              {dailyBrief.content_markdown}
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDailyBrief(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
              >
                Close
              </button>
              <button
                onClick={() => onNavigate("reports")}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-xs font-semibold text-white rounded-lg flex items-center gap-1.5"
              >
                <FileTextIcon className="w-3.5 h-3.5" />
                Go to Reports Register
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

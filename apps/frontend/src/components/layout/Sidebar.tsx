"use client";

import React from "react";
import {
  GlobeIcon,
  RadarIcon,
  NetworkIcon,
  ActivityIcon,
  CompassIcon,
  TargetIcon,
  FileTextIcon,
  SearchIcon,
  BellIcon,
  UsersIcon,
  ShieldIcon,
  CheckCircleIcon,
  BotIcon,
  SatelliteIcon,
  DatabaseIcon,
} from "../common/Icons";

export type NavSection =
  | "dashboard"
  | "map"
  | "graph"
  | "risks"
  | "scenarios"
  | "forecasts"
  | "reports"
  | "investigations"
  | "monitors"
  | "actors"
  | "claims"
  | "review"
  | "disagreements"
  | "imagery"
  | "sources"
  | "pipeline";


type SidebarProps = {
  activeSection: NavSection;
  onSelectSection: (section: NavSection) => void;
  pendingReviewCount?: number;
};

type NavGroup = {
  label: string;
  items: {
    id: NavSection;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: string | number;
    badgeVariant?: "info" | "warning" | "critical";
  }[];
};

export function Sidebar({ activeSection, onSelectSection, pendingReviewCount }: SidebarProps) {
  const navGroups: NavGroup[] = [
    {
      label: "Strategic Intelligence",
      items: [
        { id: "dashboard", label: "Overview & Dashboard", icon: RadarIcon },
        { id: "map", label: "Geospatial & Kinetic", icon: CompassIcon },
        { id: "graph", label: "Network Graph", icon: NetworkIcon },
        { id: "risks", label: "Risk Engine", icon: ActivityIcon },
      ],
    },
    {
      label: "Predictive & Assessment",
      items: [
        { id: "scenarios", label: "Scenarios & What-If", icon: GlobeIcon },
        { id: "forecasts", label: "Forecasts & Calibration", icon: TargetIcon },
        { id: "reports", label: "Executive Reports", icon: FileTextIcon },
        { id: "investigations", label: "Investigations", icon: SearchIcon },
        { id: "monitors", label: "Monitors & Alerts", icon: BellIcon },
      ],
    },
    {
      label: "Knowledge & Evidence",
      items: [
        { id: "actors", label: "Actors & Bilaterals", icon: UsersIcon },
        { id: "claims", label: "Claims & Evidence", icon: ShieldIcon },
        {
          id: "review",
          label: "Analyst Review Queue",
          icon: CheckCircleIcon,
          badge: pendingReviewCount ? pendingReviewCount : undefined,
          badgeVariant: "warning",
        },
        { id: "disagreements", label: "Multi-Model & Stances", icon: BotIcon },
        { id: "imagery", label: "Satellite & Imagery", icon: SatelliteIcon },
        { id: "sources", label: "Sources & Ingestion", icon: DatabaseIcon },
        { id: "pipeline", label: "Pipeline & Schedulers", icon: ActivityIcon },
      ],
    },
  ];


  return (
    <aside className="w-64 bg-slate-950/80 border-r border-slate-800/80 flex flex-col justify-between select-none h-[calc(100vh-4rem)] sticky top-16 overflow-y-auto custom-scrollbar">
      <div className="p-3 space-y-6">
        {navGroups.map((group) => (
          <div key={group.label}>
            <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
              {group.label}
            </div>
            <nav className="space-y-0.5">
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeSection === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onSelectSection(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition ${
                      isActive
                        ? "bg-sky-600 text-white shadow-sm font-semibold"
                        : "text-slate-400 hover:text-slate-100 hover:bg-slate-900"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Icon
                        className={`w-4 h-4 flex-shrink-0 ${
                          isActive ? "text-white" : "text-slate-400"
                        }`}
                      />
                      <span className="truncate">{item.label}</span>
                    </div>

                    {item.badge !== undefined && item.badge !== 0 && (
                      <span
                        className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                          isActive
                            ? "bg-white/20 text-white"
                            : "bg-amber-950 border border-amber-800/60 text-amber-300"
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/90 text-[11px] text-slate-400 font-mono flex items-center justify-between">
        <span>MEI PROTOCOL</span>
        <span className="text-slate-400">POSTGRES • PGVECTOR</span>
      </div>
    </aside>
  );
}

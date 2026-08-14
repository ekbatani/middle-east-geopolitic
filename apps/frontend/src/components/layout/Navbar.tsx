"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { healthService } from "../../services";
import { useAuth } from "../../context/AuthContext";
import {
  SearchIcon,
  ShieldIcon,
  ActivityIcon,
  KeyIcon,
  SparklesIcon,
  FileTextIcon,
} from "../common/Icons";
import { Badge } from "../common/Badge";
import { AuthModal } from "../common/AuthModal";
import { QuickSearchModal } from "../common/QuickSearchModal";

type NavbarProps = {
  onOpenQuickAction?: (action: string) => void;
  activeSection: string;
};

export function Navbar({ onOpenQuickAction, activeSection }: NavbarProps) {
  const { isAuthenticated, scopes } = useAuth();
  const [healthStatus, setHealthStatus] = useState<"ok" | "degraded" | "down" | "checking">("checking");
  const [healthDetails, setHealthDetails] = useState<string | null>(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  useEffect(() => {
    async function checkHealth() {
      try {
        const live = await healthService.checkLive();
        if (live.status === "ok" || live.status === "healthy") {
          setHealthStatus("ok");
          setHealthDetails("FastAPI Engine Operational");
        } else {
          setHealthStatus("degraded");
          setHealthDetails(`Status: ${live.status}`);
        }
      } catch {
        setHealthStatus("down");
        setHealthDetails("Cannot connect to API server");
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard shortcut Ctrl+K / Cmd+K for search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      <header className="sticky top-0 z-40 h-16 bg-slate-950/90 backdrop-blur-md border-b border-slate-800/80 px-6 flex items-center justify-between">
        {/* Left: Branding */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center h-9 w-9 rounded-lg bg-slate-900 border border-slate-700/80 overflow-hidden shadow-inner">
            <Image
              src="/logo.png"
              alt="MEI Intel"
              width={36}
              height={36}
              className="h-8 w-auto object-contain"
              priority
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold text-slate-100 tracking-wide">
                MIDDLE EAST INTELLIGENCE
              </h1>
              <Badge variant="info" size="sm">
                OSINT v1.0
              </Badge>
            </div>
            <p className="text-[10px] text-slate-400 font-mono">
              EVIDENCE-LED STRATEGIC MONITORING &bull; {activeSection.toUpperCase()}
            </p>
          </div>
        </div>

        {/* Center: Quick Search Bar */}
        <div className="hidden md:flex items-center flex-1 max-w-md mx-8">
          <button
            onClick={() => setIsSearchOpen(true)}
            className="w-full flex items-center justify-between px-3.5 py-1.5 bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg text-xs text-slate-400 transition shadow-inner"
          >
            <div className="flex items-center gap-2">
              <SearchIcon className="w-4 h-4 text-slate-400" />
              <span>Search actors, kinetic events, claims, documents...</span>
            </div>
            <kbd className="px-1.5 py-0.5 text-[10px] font-mono font-semibold text-slate-400 bg-slate-800 border border-slate-700 rounded">
              ⌘K
            </kbd>
          </button>
        </div>

        {/* Right: Actions, Health, Auth */}
        <div className="flex items-center gap-3">
          {/* Quick Actions Dropdown / Button */}
          {onOpenQuickAction && (
            <div className="hidden lg:flex items-center gap-2">
              <button
                onClick={() => onOpenQuickAction("daily_brief")}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-950/80 hover:bg-sky-900 border border-sky-800/60 text-xs font-semibold text-sky-200 transition"
              >
                <SparklesIcon className="w-3.5 h-3.5 text-sky-400" />
                Daily Brief
              </button>
              <button
                onClick={() => onOpenQuickAction("submit_source")}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-medium text-slate-200 transition"
              >
                <FileTextIcon className="w-3.5 h-3.5 text-slate-400" />
                Ingest URL
              </button>
            </div>
          )}

          {/* Health status badge */}
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs"
            title={healthDetails || "Checking API"}
          >
            <span className="text-[11px] text-slate-400 hidden sm:inline">Engine:</span>
            {healthStatus === "ok" ? (
              <span className="flex items-center gap-1 text-emerald-400 text-[11px] font-medium font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> LIVE
              </span>
            ) : healthStatus === "degraded" ? (
              <span className="flex items-center gap-1 text-amber-400 text-[11px] font-medium font-mono">
                <span className="w-2 h-2 rounded-full bg-amber-500" /> DEGRADED
              </span>
            ) : healthStatus === "checking" ? (
              <span className="flex items-center gap-1 text-slate-400 text-[11px] font-medium font-mono">
                <ActivityIcon className="w-3 h-3 animate-spin text-slate-400" /> PING
              </span>
            ) : (
              <span className="flex items-center gap-1 text-rose-400 text-[11px] font-medium font-mono">
                <span className="w-2 h-2 rounded-full bg-rose-500" /> OFFLINE
              </span>
            )}
          </div>

          {/* Analyst Auth button */}
          <button
            onClick={() => setIsAuthOpen(true)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition ${
              isAuthenticated
                ? "bg-emerald-950/60 border-emerald-800/60 text-emerald-200 hover:bg-emerald-900/60"
                : "bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800"
            }`}
          >
            {isAuthenticated ? (
              <>
                <ShieldIcon className="w-3.5 h-3.5 text-emerald-400" />
                <span>Analyst ({scopes.length || "Auth"})</span>
              </>
            ) : (
              <>
                <KeyIcon className="w-3.5 h-3.5 text-amber-400" />
                <span>API Key</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* Modals */}
      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
      <QuickSearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
    </>
  );
}

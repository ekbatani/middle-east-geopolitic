"use client";

import React, { useState, useEffect } from "react";
import { Modal } from "./Modal";
import { SearchItem } from "../../types";
import { intelligenceService } from "../../services";
import { SearchIcon, ActivityIcon, GlobeIcon, FileTextIcon, ShieldIcon, CheckCircleIcon } from "./Icons";
import { Badge } from "./Badge";

type QuickSearchModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onSelectResult?: (item: SearchItem) => void;
};

export function QuickSearchModal({ isOpen, onClose, onSelectResult }: QuickSearchModalProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"all" | "actor" | "event" | "claim" | "document">("all");

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const items = await intelligenceService.search(query.trim(), 40);
        setResults(items);
      } catch (err) {
        console.error("Search error:", err);
      } finally {
        setIsLoading(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  const filteredResults = activeTab === "all" ? results : results.filter((r) => r.type === activeTab);

  const getItemIcon = (type: string) => {
    switch (type) {
      case "actor":
        return <GlobeIcon className="w-4 h-4 text-sky-400" />;
      case "event":
        return <ActivityIcon className="w-4 h-4 text-rose-400" />;
      case "claim":
        return <ShieldIcon className="w-4 h-4 text-amber-400" />;
      case "document":
        return <FileTextIcon className="w-4 h-4 text-emerald-400" />;
      default:
        return <CheckCircleIcon className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Global Intelligence Search"
      subtitle="Search across state actors, verified kinetic events, claims, and archived sources"
      maxWidth="2xl"
    >
      <div className="space-y-4">
        <div className="relative">
          <input
            type="text"
            placeholder="Type actor name, event title, claim or keyword (e.g. Hormuz, IRGC, Ceasefire)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-3 bg-slate-950 border border-slate-700/80 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition"
            autoFocus
          />
          <SearchIcon className="w-5 h-5 text-slate-400 absolute left-3.5 top-3.5" />
          {isLoading && <ActivityIcon className="w-5 h-5 text-sky-400 absolute right-3.5 top-3.5 animate-spin" />}
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          {(["all", "actor", "event", "claim", "document"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1 text-xs font-medium rounded-lg transition capitalize ${
                activeTab === tab
                  ? "bg-sky-600 text-white"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              {tab === "all" ? "All Results" : `${tab}s`}
              {query && ` (${tab === "all" ? results.length : results.filter((r) => r.type === tab).length})`}
            </button>
          ))}
        </div>

        {/* Results List */}
        <div className="max-h-[50vh] overflow-y-auto space-y-2 pr-1">
          {filteredResults.length > 0 ? (
            filteredResults.map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  if (onSelectResult) onSelectResult(item);
                  onClose();
                }}
                className="p-3 bg-slate-950/60 hover:bg-slate-800/80 border border-slate-800/80 hover:border-slate-700 rounded-xl cursor-pointer transition flex items-start justify-between gap-3"
              >
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 mt-0.5">
                    {getItemIcon(item.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-100 truncate">{item.title}</span>
                      <Badge variant="neutral" size="sm">
                        {item.type}
                      </Badge>
                    </div>
                    {item.detail && (
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">{item.detail}</p>
                    )}
                  </div>
                </div>
              </div>
            ))
          ) : query.trim() && !isLoading ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              No matching intelligence entities found for &quot;{query}&quot;.
            </div>
          ) : !query.trim() ? (
            <div className="py-8 text-center text-slate-500 text-xs">
              Begin typing to query the PostgreSQL + pgvector intelligence store.
            </div>
          ) : null}
        </div>
      </div>
    </Modal>
  );
}

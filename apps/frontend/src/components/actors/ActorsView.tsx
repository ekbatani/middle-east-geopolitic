"use client";

import React, { useState, useEffect } from "react";
import {
  Actor,
  ActorTimelineResponse,
  ActorType,
  CreateActorRequest,
  CreateActorAliasRequest,
} from "../../types";
import { actorsService } from "../../services";
import {
  UsersIcon,
  PlusIcon,
  SearchIcon,
  RefreshCwIcon,
  GlobeIcon,
  UserIcon,
} from "../common/Icons";
import { Card, CardHeader } from "../common/Card";
import { Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";
import { Modal } from "../common/Modal";

export function ActorsView() {
  const [actors, setActors] = useState<Actor[]>([]);
  const [selectedActor, setSelectedActor] = useState<Actor | null>(null);
  const [timeline, setTimeline] = useState<ActorTimelineResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingTimeline, setLoadingTimeline] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [actorTypeFilter, setActorTypeFilter] = useState<ActorType | undefined>(undefined);

  // Create Actor Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState<CreateActorRequest>({
    canonical_name: "",
    actor_type: "country",
    native_name: "",
    description: "",
  });
  const [isCreating, setIsCreating] = useState(false);

  // Add Alias Modal
  const [isAliasOpen, setIsAliasOpen] = useState(false);
  const [aliasForm, setAliasForm] = useState<CreateActorAliasRequest>({
    alias: "",
    language: "ar",
  });
  const [isAddingAlias, setIsAddingAlias] = useState(false);

  const fetchActors = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await actorsService.listActors({
        q: searchQuery || undefined,
        actor_type: actorTypeFilter,
        limit: 100,
      });
      setActors(data);
    } catch (err) {
      console.error("Actors fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load actors");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(fetchActors, 200);
    return () => clearTimeout(timer);
  }, [searchQuery, actorTypeFilter]);

  const handleSelectActor = async (actor: Actor) => {
    setSelectedActor(actor);
    setLoadingTimeline(true);
    try {
      const tl = await actorsService.getActorTimeline(actor.id);
      setTimeline(tl);
    } catch (err) {
      console.error("Timeline fetch error:", err);
    } finally {
      setLoadingTimeline(false);
    }
  };

  const handleCreateActor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.canonical_name.trim()) return;

    setIsCreating(true);
    try {
      const created = await actorsService.createActor(createForm);
      setIsCreateOpen(false);
      setCreateForm({ canonical_name: "", actor_type: "country", native_name: "", description: "" });
      fetchActors();
      setSelectedActor(created);
    } catch (err) {
      console.error("Create actor error:", err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleAddAlias = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedActor || !aliasForm.alias.trim()) return;

    setIsAddingAlias(true);
    try {
      await actorsService.addActorAlias(selectedActor.id, aliasForm);
      setIsAliasOpen(false);
      setAliasForm({ alias: "", language: "ar" });
      const updated = await actorsService.getActor(selectedActor.id);
      setSelectedActor(updated);
      fetchActors();
    } catch (err) {
      console.error("Add alias error:", err);
    } finally {
      setIsAddingAlias(false);
    }
  };

  if (isLoading && actors.length === 0) {
    return <LoadingState message="Loading state actors, armed proxy networks, and leadership hierarchy..." />;
  }

  if (error && actors.length === 0) {
    return <ErrorState message={error} onRetry={fetchActors} />;
  }

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <UsersIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Actors & Regional Entity Directory
            </h2>
            <p className="text-xs text-slate-400">
              State powers &bull; Armed non-state proxies &bull; Leadership timelines & aliases
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search actors or aliases..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 w-48"
            />
            <SearchIcon className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
          </div>

          {/* Type filter */}
          <select
            value={actorTypeFilter || ""}
            onChange={(e) =>
              setActorTypeFilter(e.target.value ? (e.target.value as ActorType) : undefined)
            }
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 cursor-pointer"
          >
            <option value="" className="bg-slate-900">All Actor Types</option>
            <option value="country" className="bg-slate-900">Country</option>
            <option value="state_leader" className="bg-slate-900">State Leader</option>
            <option value="armed_non_state" className="bg-slate-900">Armed Non-State / Proxy</option>
            <option value="political_party" className="bg-slate-900">Political Party</option>
            <option value="organization" className="bg-slate-900">Organization</option>
            <option value="coalition" className="bg-slate-900">Coalition</option>
          </select>

          <button
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            <PlusIcon className="w-4 h-4" />
            Add Actor
          </button>
        </div>
      </div>

      {/* Grid Layout: Actor Directory & Detailed Profile */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Actor Cards Grid */}
        <div className="space-y-3 max-h-[calc(100vh-16rem)] overflow-y-auto pr-1">
          {actors.map((act) => {
            const isSelected = selectedActor?.id === act.id;
            return (
              <div
                key={act.id}
                onClick={() => handleSelectActor(act)}
                className={`p-4 rounded-xl border cursor-pointer transition space-y-2 ${
                  isSelected
                    ? "bg-slate-900 border-sky-500 shadow-md ring-1 ring-sky-500/20"
                    : "bg-slate-950/60 hover:bg-slate-900 border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between">
                  <Badge variant="info" size="sm">
                    {act.actor_type.replace("_", " ")}
                  </Badge>
                  <Badge variant={act.status === "active" ? "success" : "neutral"} size="sm">
                    {act.status}
                  </Badge>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-slate-100">{act.canonical_name}</h4>
                  {act.native_name && (
                    <span className="text-xs text-slate-400 font-sans">{act.native_name}</span>
                  )}
                </div>

                {act.description && (
                  <p className="text-xs text-slate-400 line-clamp-2">{act.description}</p>
                )}

                {act.aliases.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {act.aliases.map((al) => (
                      <span
                        key={al.id}
                        className="text-[10px] bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800 text-slate-400 font-mono"
                      >
                        {al.alias}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {actors.length === 0 && (
            <div className="py-12 text-center text-xs text-slate-500">
              No actors found matching filters.
            </div>
          )}
        </div>

        {/* Right 2 Columns: Selected Actor Detailed Dossier & Leadership Timeline */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="h-full flex flex-col justify-between">
            {selectedActor ? (
              <div className="space-y-6">
                {/* Profile Header */}
                <div className="border-b border-slate-800 pb-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="info">{selectedActor.actor_type.replace("_", " ")}</Badge>
                      <Badge variant={selectedActor.status === "active" ? "success" : "neutral"}>
                        {selectedActor.status}
                      </Badge>
                    </div>

                    <button
                      onClick={() => setIsAliasOpen(true)}
                      className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 font-medium rounded-lg border border-slate-700 transition"
                    >
                      + Add Alias
                    </button>
                  </div>

                  <div>
                    <h3 className="text-lg font-bold text-slate-100">
                      {selectedActor.canonical_name}
                    </h3>
                    {selectedActor.native_name && (
                      <p className="text-sm text-slate-400">{selectedActor.native_name}</p>
                    )}
                  </div>

                  {selectedActor.description && (
                    <p className="text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800 leading-relaxed">
                      {selectedActor.description}
                    </p>
                  )}
                </div>

                {/* Aliases List */}
                {selectedActor.aliases.length > 0 && (
                  <div>
                    <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono mb-2">
                      Registered Aliases & Multilingual Names
                    </h5>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedActor.aliases.map((al) => (
                        <div
                          key={al.id}
                          className="px-2.5 py-1 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-300 flex items-center gap-1.5"
                        >
                          <span className="font-semibold">{al.alias}</span>
                          {al.language && (
                            <span className="text-[10px] text-slate-500 uppercase font-mono">
                              ({al.language})
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Leadership Timeline */}
                <div>
                  <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono mb-2">
                    Leadership Hierarchy & Command Structure
                  </h5>

                  {loadingTimeline ? (
                    <LoadingState message="Loading leadership history..." />
                  ) : timeline && timeline.leadership.length > 0 ? (
                    <div className="space-y-2">
                      {timeline.leadership.map((l) => (
                        <div
                          key={l.id}
                          className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between text-xs"
                        >
                          <div className="flex items-center gap-2">
                            <UserIcon className="w-4 h-4 text-sky-400" />
                            <span className="font-semibold text-slate-200">{l.role_name}</span>
                          </div>
                          <span className="text-[11px] text-slate-500 font-mono">
                            {l.valid_from ? l.valid_from : "Tenure start"} →{" "}
                            {l.valid_to ? l.valid_to : "Present"}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="py-6 text-center text-xs text-slate-500 bg-slate-950 rounded-lg border border-slate-800">
                      No leadership records currently attached to this entity.
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-24 text-center text-slate-500 text-xs flex flex-col items-center justify-center">
                <UsersIcon className="w-8 h-8 text-slate-600 mb-2" />
                Select an actor or state power from the left list to inspect detailed profile.
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Create Actor Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Register Geopolitical Actor"
        subtitle="Add a state government, armed proxy, military command, or regional organization"
        maxWidth="md"
      >
        <form onSubmit={handleCreateActor} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Canonical Name (English)
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Islamic Revolutionary Guard Corps"
              value={createForm.canonical_name}
              onChange={(e) => setCreateForm({ ...createForm, canonical_name: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Actor Type</label>
              <select
                value={createForm.actor_type}
                onChange={(e) =>
                  setCreateForm({ ...createForm, actor_type: e.target.value as ActorType })
                }
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="country">Country</option>
                <option value="state_leader">State Leader</option>
                <option value="armed_non_state">Armed Non-State / Proxy</option>
                <option value="political_party">Political Party</option>
                <option value="organization">Organization</option>
                <option value="coalition">Coalition</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Native Name (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. سپاه پاسداران"
                value={createForm.native_name || ""}
                onChange={(e) => setCreateForm({ ...createForm, native_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
            <textarea
              rows={3}
              placeholder="Strategic mandate, command hierarchy, operational theatre..."
              value={createForm.description || ""}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
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
              {isCreating ? "Saving..." : "Create Actor"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Add Alias Modal */}
      <Modal
        isOpen={isAliasOpen}
        onClose={() => setIsAliasOpen(false)}
        title={`Add Alias for ${selectedActor?.canonical_name}`}
        subtitle="Register alternative spelling, transliteration, or native acronym"
        maxWidth="sm"
      >
        <form onSubmit={handleAddAlias} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Alias / Acronym</label>
            <input
              type="text"
              required
              placeholder="e.g. IRGC or Pasdaran"
              value={aliasForm.alias}
              onChange={(e) => setAliasForm({ ...aliasForm, alias: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Language Code</label>
            <input
              type="text"
              placeholder="e.g. ar, fa, he, en"
              value={aliasForm.language || ""}
              onChange={(e) => setAliasForm({ ...aliasForm, language: e.target.value })}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 font-mono"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsAliasOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isAddingAlias}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg transition"
            >
              {isAddingAlias ? "Adding..." : "Add Alias"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

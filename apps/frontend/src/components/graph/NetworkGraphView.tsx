"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  GraphSnapshot,
  ActorCentrality,
  GraphCommunity,
  GraphPath,
  GraphNode,
} from "../../types";
import { graphService } from "../../services";
import {
  NetworkIcon,
  RefreshCwIcon,
  ActivityIcon,
  UsersIcon,
  CompassIcon,
} from "../common/Icons";
import { Card, CardHeader } from "../common/Card";
import { Badge } from "../common/Badge";
import { LoadingState, ErrorState } from "../common/LoadingState";

export function NetworkGraphView() {
  const [snapshot, setSnapshot] = useState<GraphSnapshot | null>(null);
  const [centrality, setCentrality] = useState<ActorCentrality[]>([]);
  const [communities, setCommunities] = useState<GraphCommunity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Shortest Path Finder
  const [sourceActorId, setSourceActorId] = useState<string>("");
  const [targetActorId, setTargetActorId] = useState<string>("");
  const [pathResult, setPathResult] = useState<GraphPath | null>(null);
  const [pathLoading, setPathLoading] = useState(false);
  const [pathError, setPathError] = useState<string | null>(null);

  // Selected Node for Inspector
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const fetchGraphData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [snap, cent, comm] = await Promise.all([
        graphService.getSnapshot(),
        graphService.getCentrality(),
        graphService.getCommunities(),
      ]);
      setSnapshot(snap);
      setCentrality(cent);
      setCommunities(comm);
      if (snap.nodes.length > 0) {
        setSourceActorId(snap.nodes[0].id);
        if (snap.nodes.length > 1) {
          setTargetActorId(snap.nodes[1].id);
        }
      }
    } catch (err) {
      console.error("Graph fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load graph network");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
  }, []);

  const handleFindPath = async () => {
    if (!sourceActorId || !targetActorId) return;
    setPathLoading(true);
    setPathError(null);
    try {
      const res = await graphService.getShortestPath({
        source_actor_id: sourceActorId,
        target_actor_id: targetActorId,
      });
      setPathResult(res);
    } catch (err) {
      setPathError(err instanceof Error ? err.message : "No path found between actors");
      setPathResult(null);
    } finally {
      setPathLoading(false);
    }
  };

  // Compute 2D node positions in a circular / force-like arrangement for SVG display
  const svgWidth = 700;
  const svgHeight = 450;
  const centerX = svgWidth / 2;
  const centerY = svgHeight / 2;
  const radius = 170;

  const nodePositions = useMemo(() => {
    if (!snapshot || !snapshot.nodes.length) return new Map<string, { x: number; y: number }>();
    const map = new Map<string, { x: number; y: number }>();
    const count = snapshot.nodes.length;

    snapshot.nodes.forEach((node, idx) => {
      const angle = (idx / count) * 2 * Math.PI - Math.PI / 2;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      map.set(node.id, { x, y });
    });
    return map;
  }, [snapshot, centerX, centerY, radius]);

  // Map of actor id to name
  const actorMap = useMemo(() => {
    const m = new Map<string, string>();
    snapshot?.nodes.forEach((n) => m.set(n.id, n.canonical_name));
    return m;
  }, [snapshot]);

  if (isLoading) {
    return <LoadingState message="Computing actor network topology and influence centrality..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchGraphData} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-sky-400">
            <NetworkIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">
              Multi-Relational Actor Network Topology
            </h2>
            <p className="text-xs text-slate-400">
              Graph analytics &bull; Centrality metrics (Degree, Betweenness, Eigenvector) &bull; Influence path tracing
            </p>
          </div>
        </div>

        <button
          onClick={fetchGraphData}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
        >
          <RefreshCwIcon className="w-3.5 h-3.5" />
          Rebuild Graph
        </button>
      </div>

      {/* Main Grid: Visual Canvas & Path / Centrality Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Interactive Graph Canvas */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-0 overflow-hidden bg-slate-950 border border-slate-800">
            <div className="relative w-full aspect-[16/10] bg-[#090d16] overflow-hidden flex items-center justify-center">
              {snapshot && snapshot.nodes.length > 0 ? (
                <svg
                  viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                  className="w-full h-full select-none"
                >
                  <defs>
                    <marker
                      id="arrow"
                      viewBox="0 0 10 10"
                      refX="18"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
                    </marker>
                    <marker
                      id="arrow-path"
                      viewBox="0 0 10 10"
                      refX="18"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#38bdf8" />
                    </marker>
                  </defs>

                  {/* Graph Edges */}
                  {snapshot.edges.map((edge, i) => {
                    const src = nodePositions.get(edge.source);
                    const tgt = nodePositions.get(edge.target);
                    if (!src || !tgt) return null;

                    // Check if edge is in active shortest path
                    const inPath =
                      pathResult &&
                      pathResult.actor_ids.includes(edge.source) &&
                      pathResult.actor_ids.includes(edge.target);

                    return (
                      <g key={i}>
                        <line
                          x1={src.x}
                          y1={src.y}
                          x2={tgt.x}
                          y2={tgt.y}
                          stroke={inPath ? "#38bdf8" : "#334155"}
                          strokeWidth={inPath ? 2.5 : 1.2}
                          strokeDasharray={edge.relationship_type.includes("proxy") ? "3 3" : undefined}
                          markerEnd={inPath ? "url(#arrow-path)" : "url(#arrow)"}
                        />
                        {/* Midpoint Label for relationship type */}
                        <text
                          x={(src.x + tgt.x) / 2}
                          y={(src.y + tgt.y) / 2 - 4}
                          fill={inPath ? "#38bdf8" : "#64748b"}
                          fontSize="8"
                          textAnchor="middle"
                          fontFamily="monospace"
                          className="pointer-events-none"
                        >
                          {edge.relationship_type}
                        </text>
                      </g>
                    );
                  })}

                  {/* Graph Nodes */}
                  {snapshot.nodes.map((node) => {
                    const pos = nodePositions.get(node.id);
                    if (!pos) return null;

                    const isSelected = selectedNode?.id === node.id;
                    const inPath = pathResult?.actor_ids.includes(node.id);
                    const isCountry = node.actor_type === "country";

                    return (
                      <g
                        key={node.id}
                        transform={`translate(${pos.x}, ${pos.y})`}
                        onClick={() => setSelectedNode(node)}
                        className="cursor-pointer transition hover:opacity-100"
                      >
                        {isSelected && (
                          <circle r="18" fill="none" stroke="#38bdf8" strokeWidth="2" strokeDasharray="3 3" />
                        )}
                        <circle
                          r={isCountry ? "12" : "9"}
                          fill={inPath ? "#0284c7" : isCountry ? "#1e293b" : "#334155"}
                          stroke={inPath ? "#38bdf8" : isCountry ? "#38bdf8" : "#94a3b8"}
                          strokeWidth="2"
                        />
                        <text
                          x="0"
                          y="4"
                          textAnchor="middle"
                          fill="#ffffff"
                          fontSize="9"
                          fontWeight="bold"
                          className="pointer-events-none font-mono"
                        >
                          {node.canonical_name.slice(0, 3).toUpperCase()}
                        </text>
                        {/* Full label below */}
                        <text
                          x="0"
                          y="22"
                          textAnchor="middle"
                          fill={isSelected ? "#38bdf8" : "#cbd5e1"}
                          fontSize="9"
                          fontWeight={isSelected ? "bold" : "normal"}
                          className="pointer-events-none bg-slate-950/80 drop-shadow"
                        >
                          {node.canonical_name}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              ) : (
                <div className="text-xs text-slate-500">No network nodes available.</div>
              )}
            </div>
          </Card>

          {/* Shortest Path Finder Bar */}
          <Card>
            <CardHeader
              title="Bilateral Influence & Shortest Path Finder"
              subtitle="Trace the shortest relational chain between any two regional entities"
              icon={<CompassIcon className="w-5 h-5" />}
            />

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <div className="flex-1 w-full">
                <label className="block text-[11px] font-mono text-slate-400 mb-1">Source Actor</label>
                <select
                  value={sourceActorId}
                  onChange={(e) => setSourceActorId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  {snapshot?.nodes.map((n) => (
                    <option key={n.id} value={n.id} className="bg-slate-900">
                      {n.canonical_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="text-slate-500 font-bold hidden sm:block pt-5">&rarr;</div>

              <div className="flex-1 w-full">
                <label className="block text-[11px] font-mono text-slate-400 mb-1">Target Actor</label>
                <select
                  value={targetActorId}
                  onChange={(e) => setTargetActorId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                >
                  {snapshot?.nodes.map((n) => (
                    <option key={n.id} value={n.id} className="bg-slate-900">
                      {n.canonical_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-0 sm:pt-5 w-full sm:w-auto">
                <button
                  onClick={handleFindPath}
                  disabled={pathLoading || sourceActorId === targetActorId}
                  className="w-full sm:w-auto px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-xs font-semibold text-white rounded-lg transition"
                >
                  {pathLoading ? "Tracing..." : "Find Path"}
                </button>
              </div>
            </div>

            {/* Path Result display */}
            {pathResult && (
              <div className="mt-4 p-3 bg-sky-950/30 border border-sky-800/40 rounded-xl space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-sky-300">
                    Direct Chain Found ({pathResult.length} hops)
                  </span>
                  <Badge variant="info">Shortest Path</Badge>
                </div>
                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-200 pt-1">
                  {pathResult.actor_ids.map((id, idx) => (
                    <React.Fragment key={id}>
                      <span className="bg-slate-900 px-2.5 py-1 rounded-md border border-slate-700 font-medium">
                        {actorMap.get(id) || id}
                      </span>
                      {idx < pathResult.actor_ids.length - 1 && (
                        <span className="text-sky-400 font-bold">&rarr;</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            )}

            {pathError && (
              <div className="mt-3 p-3 bg-rose-950/30 border border-rose-800/40 text-xs text-rose-300 rounded-lg">
                {pathError}
              </div>
            )}
          </Card>
        </div>

        {/* Right Col: Centrality Leaderboard & Communities */}
        <div className="space-y-4">
          <Card>
            <CardHeader
              title="Influence Centrality Scores"
              subtitle="Network hub rankings computed via graph algorithms"
              icon={<ActivityIcon className="w-5 h-5" />}
            />

            <div className="space-y-2 max-h-[340px] overflow-y-auto pr-1">
              {centrality.slice(0, 10).map((c, i) => (
                <div
                  key={c.actor_id}
                  className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg space-y-1 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">
                      {i + 1}. {c.canonical_name}
                    </span>
                    <Badge variant="info" size="sm">
                      Deg: {c.degree_centrality.toFixed(2)}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-400 font-mono pt-1 border-t border-slate-900">
                    <span>Betweenness: {c.betweenness_centrality.toFixed(3)}</span>
                    <span>Eigenvector: {c.eigenvector_centrality.toFixed(3)}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Communities */}
          <Card>
            <CardHeader
              title="Detected Coalitions & Clusters"
              subtitle="Community detection partitions"
              icon={<UsersIcon className="w-5 h-5" />}
            />

            <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
              {communities.map((comm) => (
                <div
                  key={comm.index}
                  className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg space-y-1 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-300">
                      Cluster #{comm.index + 1}
                    </span>
                    <Badge variant="neutral" size="sm">
                      {comm.actor_ids.length} Actors
                    </Badge>
                  </div>
                  <div className="text-[11px] text-slate-400 line-clamp-2">
                    {comm.actor_ids.map((id) => actorMap.get(id) || id).join(", ")}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

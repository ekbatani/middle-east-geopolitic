import { UUID } from "./common";

export type ActorCentrality = {
  actor_id: UUID;
  canonical_name: string;
  degree_centrality: number;
  betweenness_centrality: number;
  eigenvector_centrality: number;
};

export type GraphPath = {
  actor_ids: UUID[];
  length: number;
};

export type GraphCommunity = {
  index: number;
  actor_ids: UUID[];
};

export type GraphNode = {
  id: UUID;
  canonical_name: string;
  actor_type?: string | null;
};

export type GraphEdge = {
  source: UUID;
  target: UUID;
  relationship_type: string;
  weight: number;
};

export type GraphSnapshot = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

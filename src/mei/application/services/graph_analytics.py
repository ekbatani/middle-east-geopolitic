from __future__ import annotations

from typing import TypedDict
from uuid import UUID

import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from mei.infrastructure.repositories.actors import ActorRepository
from mei.infrastructure.repositories.relationships import RelationshipRepository
from mei.shared.enums import RelationshipStatus

_DEFAULT_EDGE_WEIGHT = 1.0


class CentralityScores(TypedDict):
    degree: float
    betweenness: float
    eigenvector: float


class GraphAnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._relationships = RelationshipRepository(session)
        self._actors = ActorRepository(session)

    async def build_actor_graph(
        self, *, relationship_status: RelationshipStatus | None = RelationshipStatus.ACTIVE
    ) -> nx.Graph:
        """Load actors and relationships into an in-memory `networkx.Graph`
        (design doc section 35, Phase 6 "graph analytics").

        Edge weight is the latest `escalation_risk_score` observation when
        one exists, else a flat default — relationships with no scored
        observation yet still participate in path/community analysis, just
        without a meaningful weight.
        """
        relationships = await self._relationships.list_all(status=relationship_status, limit=10_000)

        actor_ids = {r.source_actor_id for r in relationships} | {
            r.target_actor_id for r in relationships
        }
        actors = await self._actors.list_by_ids(list(actor_ids))
        actors_by_id = {actor.id: actor for actor in actors}

        graph: nx.Graph = nx.Graph()
        for actor_id in actor_ids:
            actor = actors_by_id.get(actor_id)
            graph.add_node(
                actor_id,
                canonical_name=actor.canonical_name if actor else str(actor_id),
                actor_type=str(actor.actor_type) if actor else None,
            )

        for relationship in relationships:
            observation = await self._relationships.get_latest_observation(relationship.id)
            weight = _DEFAULT_EDGE_WEIGHT
            if observation is not None and observation.escalation_risk_score is not None:
                weight = float(observation.escalation_risk_score)
            graph.add_edge(
                relationship.source_actor_id,
                relationship.target_actor_id,
                relationship_id=relationship.id,
                relationship_type=relationship.relationship_type,
                weight=weight,
            )

        return graph


def compute_centrality(graph: nx.Graph) -> dict[UUID, CentralityScores]:
    """Degree/betweenness/eigenvector centrality for every node.

    Pure and DB-free so it's directly unit-testable against hand-built
    graphs. Eigenvector centrality can fail to converge on some graph
    shapes (disconnected graphs, graphs with no edges) — those nodes get
    `0.0` rather than raising, since "not centrally connected" is exactly
    what that failure means here.
    """
    if graph.number_of_nodes() == 0:
        return {}

    degree = nx.degree_centrality(graph)
    betweenness = nx.betweenness_centrality(graph, weight="weight")
    try:
        eigenvector = nx.eigenvector_centrality(graph, weight="weight", max_iter=1000)
    except (nx.NetworkXException, ZeroDivisionError):
        eigenvector = dict.fromkeys(graph.nodes, 0.0)

    return {
        node: CentralityScores(
            degree=degree.get(node, 0.0),
            betweenness=betweenness.get(node, 0.0),
            eigenvector=eigenvector.get(node, 0.0),
        )
        for node in graph.nodes
    }


def shortest_path(graph: nx.Graph, source: UUID, target: UUID) -> list[UUID] | None:
    """Shortest weighted path between two actors, or `None` if either node
    is missing or they're disconnected."""
    if source not in graph or target not in graph:
        return None
    try:
        return list(nx.shortest_path(graph, source=source, target=target, weight="weight"))
    except nx.NetworkXNoPath:
        return None


def detect_communities(graph: nx.Graph) -> list[list[UUID]]:
    """Greedy-modularity community detection. A graph with no edges has no
    meaningful communities to detect, so each node is returned as its own
    singleton community rather than calling into an algorithm that assumes
    at least one edge exists."""
    if graph.number_of_edges() == 0:
        return [[node] for node in graph.nodes]

    communities = nx.algorithms.community.greedy_modularity_communities(graph, weight="weight")
    return [list(community) for community in communities]


__all__ = [
    "CentralityScores",
    "GraphAnalyticsService",
    "compute_centrality",
    "detect_communities",
    "shortest_path",
]

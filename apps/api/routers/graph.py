"""Actor-relationship graph analytics (design doc section 35, Phase 6)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.graph_analytics import (
    GraphAnalyticsService,
    compute_centrality,
    detect_communities,
    shortest_path,
)
from mei.infrastructure.auth.principal import Principal
from mei.shared.enums import RelationshipStatus, Scope
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/graph", tags=["graph"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]


class ActorCentralityOut(BaseModel):
    actor_id: UUID
    canonical_name: str
    degree_centrality: float
    betweenness_centrality: float
    eigenvector_centrality: float


class PathOut(BaseModel):
    actor_ids: list[UUID]
    length: int


class CommunityOut(BaseModel):
    index: int
    actor_ids: list[UUID]


class GraphNodeOut(BaseModel):
    id: UUID
    canonical_name: str
    actor_type: str | None


class GraphEdgeOut(BaseModel):
    source: UUID
    target: UUID
    relationship_type: str
    weight: float


class GraphSnapshotOut(BaseModel):
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]


@router.get("/centrality", response_model=list[ActorCentralityOut])
async def get_centrality(
    session: SessionDep,
    _principal: ReadPrincipal,
    relationship_status: RelationshipStatus | None = RelationshipStatus.ACTIVE,
) -> list[ActorCentralityOut]:
    graph = await GraphAnalyticsService(session).build_actor_graph(
        relationship_status=relationship_status
    )
    scores = compute_centrality(graph)
    return [
        ActorCentralityOut(
            actor_id=actor_id,
            canonical_name=graph.nodes[actor_id]["canonical_name"],
            degree_centrality=score["degree"],
            betweenness_centrality=score["betweenness"],
            eigenvector_centrality=score["eigenvector"],
        )
        for actor_id, score in scores.items()
    ]


@router.get("/path", response_model=PathOut)
async def get_path(
    session: SessionDep,
    _principal: ReadPrincipal,
    source_actor_id: UUID,
    target_actor_id: UUID,
    relationship_status: RelationshipStatus | None = RelationshipStatus.ACTIVE,
) -> PathOut:
    graph = await GraphAnalyticsService(session).build_actor_graph(
        relationship_status=relationship_status
    )
    path = shortest_path(graph, source_actor_id, target_actor_id)
    if path is None:
        raise NotFoundError(
            f"No path between {source_actor_id} and {target_actor_id} in the current graph"
        )
    return PathOut(actor_ids=path, length=len(path) - 1)


@router.get("/communities", response_model=list[CommunityOut])
async def get_communities(
    session: SessionDep,
    _principal: ReadPrincipal,
    relationship_status: RelationshipStatus | None = RelationshipStatus.ACTIVE,
) -> list[CommunityOut]:
    graph = await GraphAnalyticsService(session).build_actor_graph(
        relationship_status=relationship_status
    )
    communities = detect_communities(graph)
    return [
        CommunityOut(index=index, actor_ids=list(community))
        for index, community in enumerate(communities)
    ]


@router.get("/snapshot", response_model=GraphSnapshotOut)
async def get_snapshot(
    session: SessionDep,
    _principal: ReadPrincipal,
    relationship_status: RelationshipStatus | None = RelationshipStatus.ACTIVE,
) -> GraphSnapshotOut:
    graph = await GraphAnalyticsService(session).build_actor_graph(
        relationship_status=relationship_status
    )
    nodes = [
        GraphNodeOut(
            id=node_id, canonical_name=data["canonical_name"], actor_type=data["actor_type"]
        )
        for node_id, data in graph.nodes(data=True)
    ]
    edges = [
        GraphEdgeOut(
            source=source,
            target=target,
            relationship_type=data["relationship_type"],
            weight=data["weight"],
        )
        for source, target, data in graph.edges(data=True)
    ]
    return GraphSnapshotOut(nodes=nodes, edges=edges)

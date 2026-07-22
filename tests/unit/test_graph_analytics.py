from uuid import UUID, uuid4

import networkx as nx
from hypothesis import given
from hypothesis import strategies as st

from mei.application.services.graph_analytics import (
    compute_centrality,
    detect_communities,
    shortest_path,
)


def _star_graph(leaf_count: int) -> tuple[nx.Graph, UUID, list[UUID]]:
    """A hub actor connected to `leaf_count` independent leaf actors."""
    graph: nx.Graph = nx.Graph()
    hub = uuid4()
    leaves = [uuid4() for _ in range(leaf_count)]
    graph.add_node(hub, canonical_name="Hub", actor_type="country")
    for leaf in leaves:
        graph.add_node(leaf, canonical_name="Leaf", actor_type="country")
        graph.add_edge(hub, leaf, relationship_id=uuid4(), relationship_type="ally", weight=1.0)
    return graph, hub, leaves


def test_compute_centrality_empty_graph_returns_empty_mapping() -> None:
    assert compute_centrality(nx.Graph()) == {}


def test_compute_centrality_disconnected_node_has_zero_degree() -> None:
    # A single-node graph is a degenerate case networkx defines as centrality
    # 1 by convention; a genuinely disconnected node (no edges, but not the
    # graph's only node) is the meaningful "not centrally connected" case.
    graph: nx.Graph = nx.Graph()
    isolated, other = uuid4(), uuid4()
    graph.add_node(isolated, canonical_name="Isolated", actor_type="country")
    graph.add_node(other, canonical_name="Other", actor_type="country")
    scores = compute_centrality(graph)
    assert scores[isolated]["degree"] == 0.0
    assert scores[isolated]["betweenness"] == 0.0


def test_compute_centrality_hub_has_higher_degree_than_leaves() -> None:
    graph, hub, leaves = _star_graph(4)
    scores = compute_centrality(graph)
    assert scores[hub]["degree"] > scores[leaves[0]]["degree"]


def test_shortest_path_missing_node_returns_none() -> None:
    graph, hub, _ = _star_graph(2)
    assert shortest_path(graph, hub, uuid4()) is None


def test_shortest_path_disconnected_nodes_return_none() -> None:
    graph: nx.Graph = nx.Graph()
    a, b = uuid4(), uuid4()
    graph.add_node(a, canonical_name="A", actor_type="country")
    graph.add_node(b, canonical_name="B", actor_type="country")
    assert shortest_path(graph, a, b) is None


def test_shortest_path_between_leaves_goes_through_hub() -> None:
    graph, hub, leaves = _star_graph(2)
    path = shortest_path(graph, leaves[0], leaves[1])
    assert path == [leaves[0], hub, leaves[1]]


def test_detect_communities_no_edges_returns_singletons() -> None:
    graph: nx.Graph = nx.Graph()
    a, b = uuid4(), uuid4()
    graph.add_node(a, canonical_name="A", actor_type="country")
    graph.add_node(b, canonical_name="B", actor_type="country")
    communities = detect_communities(graph)
    assert sorted(len(c) for c in communities) == [1, 1]
    assert {a, b} == {node for community in communities for node in community}


@given(leaf_count=st.integers(min_value=1, max_value=8))
def test_star_graph_every_connected_node_has_positive_degree(leaf_count: int) -> None:
    graph, hub, leaves = _star_graph(leaf_count)
    scores = compute_centrality(graph)
    assert scores[hub]["degree"] > 0
    for leaf in leaves:
        assert scores[leaf]["degree"] > 0


@given(leaf_count=st.integers(min_value=1, max_value=8))
def test_star_graph_path_between_any_two_leaves_has_length_two(leaf_count: int) -> None:
    if leaf_count < 2:
        return
    graph, _hub, leaves = _star_graph(leaf_count)
    path = shortest_path(graph, leaves[0], leaves[1])
    assert path is not None
    assert len(path) - 1 == 2

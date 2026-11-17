import pytest

from sentinel.knowledge.graph import KnowledgeGraph


def test_graph_nodes_edges_and_provenance():
    graph = KnowledgeGraph()
    graph.add_node("person:1", "Ada", role="engineer")
    graph.add_node("project:1", "Sentinel")
    edge = graph.add_edge("person:1", "works_on", "project:1", provenance="user")
    assert edge.provenance == "user"
    assert graph.neighbors("person:1")[0][1].label == "Sentinel"
    assert graph.find("ada")[0].node_id == "person:1"


def test_graph_rejects_missing_endpoints_and_conflicting_nodes():
    graph = KnowledgeGraph()
    graph.add_node("a", "A")
    with pytest.raises(KeyError):
        graph.add_edge("a", "links", "missing")
    with pytest.raises(ValueError):
        graph.add_node("a", "Different")

def test_graph_persistence_round_trip(tmp_path):
    from sentinel.storage.backends.sqlite import SQLiteBackend
    graph = KnowledgeGraph()
    graph.add_node("a", "Alpha", kind="topic")
    graph.add_node("b", "Beta")
    graph.add_edge("a", "relates_to", "b", provenance="import")
    backend = SQLiteBackend(tmp_path / "graph.db")
    graph.persist(backend)
    restored = KnowledgeGraph.restore(backend)
    assert restored.snapshot() == graph.snapshot()
    backend.close()

@pytest.mark.parametrize(
    "node",
    [
        {"label": "Missing ID"},
        {"node_id": "a"},
        {"node_id": None, "label": "Invalid ID"},
        {"node_id": "a", "label": None},
        {"node_id": "a", "label": "A", "properties": {"kind": 1}},
    ],
)
def test_graph_restore_rejects_invalid_nodes(node):
    from sentinel.knowledge.graph import KnowledgeGraph

    class Backend:
        def get(self, key):
            import json
            return json.dumps({"version": 1, "nodes": [node], "edges": []})

    with pytest.raises(ValueError):
        KnowledgeGraph.restore(Backend())


@pytest.mark.parametrize(
    "edge",
    [
        {"relation": "links", "target": "b"},
        {"source": "a", "target": "b"},
        {"source": None, "relation": "links", "target": "b"},
        {"source": "a", "relation": "links", "target": None},
        {
            "source": "a",
            "relation": "links",
            "target": "b",
            "provenance": 123,
        },
    ],
)
def test_graph_restore_rejects_invalid_edges(edge):
    from sentinel.knowledge.graph import KnowledgeGraph

    class Backend:
        def get(self, key):
            import json
            return json.dumps({"version": 1, "nodes": [], "edges": [edge]})

    with pytest.raises(ValueError):
        KnowledgeGraph.restore(Backend())
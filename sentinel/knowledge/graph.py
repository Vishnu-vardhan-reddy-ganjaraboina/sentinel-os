"""Small deterministic knowledge graph with explicit provenance."""

from __future__ import annotations

import json
from dataclasses import dataclass
from threading import RLock
from typing import Any

from sentinel.storage.interfaces import StorageBackend


@dataclass(frozen=True, slots=True)
class KnowledgeNode:
    node_id: str
    label: str
    properties: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class KnowledgeEdge:
    source: str
    relation: str
    target: str
    provenance: str | None = None


class KnowledgeGraph:
    """In-memory graph; callers decide persistence and tenant partitioning."""

    def __init__(self) -> None:
        self._nodes: dict[str, KnowledgeNode] = {}
        self._edges: set[KnowledgeEdge] = set()
        self._lock = RLock()

    def add_node(self, node_id: str, label: str, **properties: str) -> KnowledgeNode:
        if (
            not isinstance(node_id, str)
            or not node_id.strip()
            or not isinstance(label, str)
            or not label.strip()
        ):
            raise ValueError("node_id and label must be non-empty strings")
        if any(
            not isinstance(k, str) or not isinstance(v, str)
            for k, v in properties.items()
        ):
            raise TypeError("node properties must be string pairs")
        node = KnowledgeNode(node_id, label, tuple(sorted(properties.items())))
        with self._lock:
            existing = self._nodes.get(node_id)
            if existing is not None and existing != node:
                raise ValueError(f"node {node_id!r} already exists with different data")
            self._nodes[node_id] = node
        return node

    def add_edge(
        self, source: str, relation: str, target: str, *, provenance: str | None = None
    ) -> KnowledgeEdge:
        if not all(
            isinstance(x, str) and x.strip() for x in (source, relation, target)
        ):
            raise ValueError("source, relation and target must be non-empty strings")
        edge = KnowledgeEdge(source, relation, target, provenance)
        with self._lock:
            if source not in self._nodes or target not in self._nodes:
                raise KeyError("both edge endpoints must exist")
            self._edges.add(edge)
        return edge

    def neighbors(
        self, node_id: str, *, relation: str | None = None
    ) -> list[tuple[KnowledgeEdge, KnowledgeNode]]:
        with self._lock:
            if node_id not in self._nodes:
                raise KeyError(node_id)
            return [
                (edge, self._nodes[edge.target])
                for edge in sorted(
                    self._edges, key=lambda e: (e.source, e.relation, e.target)
                )
                if edge.source == node_id
                and (relation is None or edge.relation == relation)
            ]

    def find(self, text: str) -> list[KnowledgeNode]:
        query = text.casefold().strip()
        if not query:
            return []
        with self._lock:
            return [
                node
                for node in sorted(self._nodes.values(), key=lambda n: n.node_id)
                if query in node.label.casefold()
            ]

    def snapshot(self) -> tuple[tuple[KnowledgeNode, ...], tuple[KnowledgeEdge, ...]]:
        with self._lock:
            return tuple(sorted(self._nodes.values(), key=lambda n: n.node_id)), tuple(
                sorted(self._edges, key=lambda e: (e.source, e.relation, e.target))
            )

    def persist(
        self, backend: StorageBackend, key: str = "sentinel:knowledge:graph"
    ) -> None:
        """Persist a deterministic JSON snapshot through the supplied backend.

        Pass EncryptedStorageBackend when graph content must be encrypted at rest.
        """
        nodes, edges = self.snapshot()
        payload: dict[str, Any] = {
            "version": 1,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "label": n.label,
                    "properties": dict(n.properties),
                }
                for n in nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "relation": e.relation,
                    "target": e.target,
                    "provenance": e.provenance,
                }
                for e in edges
            ],
        }
        with backend.atomic():
            backend.set(
                key,
                json.dumps(
                    payload, ensure_ascii=False, allow_nan=False, sort_keys=True
                ),
            )

    @classmethod
    def restore(
        cls, backend: StorageBackend, key: str = "sentinel:knowledge:graph"
    ) -> KnowledgeGraph:
        """Restore a validated graph snapshot.

        Executable serialization is never used.
        """
        raw = backend.get(key)
        if not isinstance(raw, str):
            raise ValueError("knowledge graph snapshot must be JSON text")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("knowledge graph snapshot is invalid JSON") from exc
        if not isinstance(payload, dict) or payload.get("version") != 1:
            raise ValueError("unsupported knowledge graph snapshot version")
        nodes, edges = payload.get("nodes"), payload.get("edges")
        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise ValueError("knowledge graph snapshot has invalid collections")
        graph = cls()
        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError("invalid knowledge graph node")

            node_id = node.get("node_id")
            label = node.get("label")
            properties = node.get("properties", {})

            if (
                not isinstance(node_id, str)
                or not node_id.strip()
                or not isinstance(label, str)
                or not label.strip()
                or not isinstance(properties, dict)
            ):
                raise ValueError("invalid knowledge graph node")

            if any(
                not isinstance(name, str) or not isinstance(value, str)
                for name, value in properties.items()
            ):
                raise ValueError("invalid knowledge graph node properties")

            graph.add_node(node_id, label, **properties)

        for edge in edges:
            if not isinstance(edge, dict):
                raise ValueError("invalid knowledge graph edge")

            source = edge.get("source")
            relation = edge.get("relation")
            target = edge.get("target")
            provenance = edge.get("provenance")

            if (
                not isinstance(source, str)
                or not source.strip()
                or not isinstance(relation, str)
                or not relation.strip()
                or not isinstance(target, str)
                or not target.strip()
                or (provenance is not None and not isinstance(provenance, str))
            ):
                raise ValueError("invalid knowledge graph edge")

            graph.add_edge(
                source,
                relation,
                target,
                provenance=provenance,
            )
        return graph

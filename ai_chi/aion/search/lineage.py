"""Source lineage graph — anti-slop provenance edges.

Tracks CLAIMS / CITES / COPIES / LAUNDERS_SOURCE edges between sources so the
system can tell original reporting from laundered copies. A laundering path is a
chain of COPIES/LAUNDERS_SOURCE edges that hides an original source.
"""
from __future__ import annotations

from collections import defaultdict

from .models import SourceLineageEdge, Relation

_LAUNDERING = {Relation.COPIES, Relation.LAUNDERS_SOURCE}


class LineageGraph:
    def __init__(self):
        self._out = defaultdict(list)   # src -> [SourceLineageEdge]

    def add_edge(self, src: str, dst: str, relation) -> None:
        self._out[src].append(SourceLineageEdge(src, dst, relation))

    def neighbors(self, src: str):
        return list(self._out.get(src, []))

    def launders(self, src: str, max_depth: int = 8) -> bool:
        """True if, from src, at least one COPIES/LAUNDERS_SOURCE edge is traversed
        on the way to an originator (a node that CLAIMS, or a dead end)."""
        seen = set()

        def is_origin(node) -> bool:
            edges = self._out.get(node, [])
            return (not edges) or any(e.relation is Relation.CLAIMS for e in edges)

        def walk(node, depth, used_launder):
            if depth > max_depth:
                return False
            if used_launder and is_origin(node):
                return True
            if node in seen:
                return False
            seen.add(node)
            for e in self._out.get(node, []):
                nl = used_launder or (e.relation in _LAUNDERING)
                if walk(e.dst, depth + 1, nl):
                    return True
            return False

        return walk(src, 0, False)

    def original_sources(self, src: str, max_depth: int = 8):
        """Best-effort: nodes reachable that themselves only CLAIMS (originators)."""
        origins, seen = [], set()

        def walk(node, depth):
            if depth > max_depth or node in seen:
                return
            seen.add(node)
            edges = self._out.get(node, [])
            claims = [e for e in edges if e.relation is Relation.CLAIMS]
            if claims or not edges:
                origins.append(node)
            for e in edges:
                walk(e.dst, depth + 1)

        walk(src, 0)
        return origins

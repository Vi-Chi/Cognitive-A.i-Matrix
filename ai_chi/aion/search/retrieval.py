"""Three-index retrieval with a ranking-explanation contract.

Three deterministic indexes, merged by weighted fusion:
  * lexical — token-overlap (Jaccard)
  * vector  — STUB pseudo-embedding (hashed token bag cosine). Marked clearly;
    swap for a real embedder behind this interface later. Deterministic so tests
    are stable and offline.
  * graph   — lineage trust boost (originals > laundered copies)

Every returned doc carries a RankingExplanation (the contract): the per-index
signals that produced its rank. Invariant surfaced on every explanation:
"high rank != high truth; retrieved != true".
"""
from __future__ import annotations

import math
import re
from collections import Counter

from .models import RetrievalResult, RankingExplanation

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str):
    return _TOKEN.findall((text or "").lower())


def _lexical(query, text) -> float:
    q, d = set(_tokens(query)), set(_tokens(text))
    if not q or not d:
        return 0.0
    return len(q & d) / len(q | d)


def _bag(text):
    return Counter(_tokens(text))


def _vector_stub(query, text) -> float:
    """Deterministic cosine over raw token-count bags. STUB embedder."""
    a, b = _bag(query), _bag(text)
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


class ThreeIndexRetriever:
    def __init__(self, weights=None, lineage=None):
        self.weights = weights or {"lexical": 0.4, "vector": 0.4, "graph": 0.2}
        self.lineage = lineage   # optional LineageGraph for the graph index

    def _graph_signal(self, doc_id) -> float:
        if self.lineage is None:
            return 0.0
        # laundered copies are penalised; clean/original sources get a small boost
        return -0.5 if self.lineage.launders(doc_id) else 0.25

    def retrieve(self, query: str, docs: dict):
        """docs: {doc_id: text}. Returns (ranked_results, explanations)."""
        scored = []
        for doc_id, text in docs.items():
            sig = {
                "lexical": _lexical(query, text),
                "vector": _vector_stub(query, text),
                "graph": self._graph_signal(doc_id),
            }
            final = sum(self.weights[k] * sig[k] for k in self.weights)
            scored.append((doc_id, final, sig))

        scored.sort(key=lambda t: t[1], reverse=True)

        results, explanations = [], []
        for rank, (doc_id, final, sig) in enumerate(scored, start=1):
            results.append(RetrievalResult(doc_id=doc_id, score=final, index="fused"))
            explanations.append(RankingExplanation(
                query=query, doc_id=doc_id, final_rank=rank, final_score=final,
                signals=sig,
                notes=["fused = " + " + ".join(
                    f"{self.weights[k]}*{k}" for k in self.weights)],
            ))
        return results, explanations

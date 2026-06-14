"""AION-SEARCH — a memory membrane for the open web.

AIDICT generalised from AI-dev claims to the open web and to search engines
themselves. Reuses the AION Reality Loop: observe -> rank-memory -> retrieve ->
audit -> divergence-preserve -> promote.

Epistemic invariants (never relaxed):
    Retrieved != True
    Cited     != Verified
    Popular   != Authoritative
    High rank != High truth

Original layer vs AIDICT: AION-SEARCH stores not only *content* but *ranking
memory* — how search systems chose visibility over time (SERP snapshot ledger,
a fossil record). Competing engines are preserved as epistemic branches, not
merged.
"""
from .models import (
    PromotionState, Relation, RankingObservation, SerpSnapshot,
    SourceLineageEdge, RetrievalResult, RankingExplanation, SearchClaim,
)
from .ranking_memory import RankingMemory
from .lineage import LineageGraph
from .retrieval import ThreeIndexRetriever
from .promotion import SearchPromotion

__all__ = [
    "PromotionState", "Relation", "RankingObservation", "SerpSnapshot",
    "SourceLineageEdge", "RetrievalResult", "RankingExplanation", "SearchClaim",
    "RankingMemory", "LineageGraph", "ThreeIndexRetriever", "SearchPromotion",
]

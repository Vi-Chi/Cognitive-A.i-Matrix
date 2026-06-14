"""AION-SEARCH data models (stdlib dataclasses + enums)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, IntEnum


class PromotionState(IntEnum):
    """A search claim's promotion chain. A claim may not skip a rung."""
    OBSERVED = 0       # seen in a SERP / page
    CITED = 1          # something cites it
    CORROBORATED = 2   # independent source agrees
    AUDITED = 3        # Urbi audited (out-of-loop)
    PROMOTED = 4       # eligible to inform action

    @property
    def label(self) -> str:
        return self.name.capitalize()


class Relation(Enum):
    """Source-lineage edge types (anti-slop)."""
    CLAIMS = "claims"
    CITES = "cites"
    COPIES = "copies"
    LAUNDERS_SOURCE = "launders_source"


@dataclass
class RankingObservation:
    """One ranked result as observed in a SERP at a point in time."""
    url: str
    rank: int
    engine: str
    query: str
    title: str = ""
    snippet: str = ""
    captured_at: float = field(default_factory=time.time)


@dataclass
class SerpSnapshot:
    """A fossil record of one search at one moment from one engine."""
    query: str
    engine: str
    observations: list = field(default_factory=list)
    captured_at: float = field(default_factory=time.time)


@dataclass
class SourceLineageEdge:
    src: str
    dst: str
    relation: Relation

    def __post_init__(self):
        if not isinstance(self.relation, Relation):
            self.relation = Relation(self.relation)


@dataclass
class RetrievalResult:
    doc_id: str
    score: float
    index: str        # "lexical" | "vector" | "graph"


@dataclass
class RankingExplanation:
    """The ranking explanation contract — why a doc holds its rank."""
    query: str
    doc_id: str
    final_rank: int
    final_score: float
    signals: dict = field(default_factory=dict)   # per-index contributions
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query": self.query, "doc_id": self.doc_id,
            "final_rank": self.final_rank, "final_score": round(self.final_score, 6),
            "signals": {k: round(v, 6) for k, v in self.signals.items()},
            "notes": list(self.notes),
            "invariant": "high rank != high truth; retrieved != true",
        }


@dataclass
class SearchClaim:
    """A claim extracted from the open web, tracked up the promotion chain."""
    id: str
    text: str
    source_url: str
    state: PromotionState = PromotionState.OBSERVED
    corroborations: list = field(default_factory=list)
    audited_by: str = ""
    history: list = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.state, PromotionState):
            self.state = PromotionState(self.state)

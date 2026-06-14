"""AION — Archetypal Intelligence Ontology Network.

The Cognitive Matrix ontology layer: organize, classify, compare and audit
recurring patterns across domains, then gate whether a pattern may influence
Orbi action.

Core rule (AION safety invariant):
    Pattern recognition must be audited before it becomes power.

AION may discover/compare/preserve/propose patterns. AION may NOT promote a
pattern into system truth, tool routing, physical/cloud/on-chain control, or
autonomous action without evidence classification, contradiction scanning,
Urbi audit, and MΣBUS gating.

Triad placement: AION sits *under* the constitution.
    Urbi  audits/classifies/vetoes (never acts)
    Orbi  executes contracted patterns (never self-audits)
    MΣBUS enforces provenance/transfer/action gates (never judges or acts)
"""
from .ontology import (
    EvidenceLevel,
    TransferLevel,
    RiskClass,
    TrustState,
    Sensitivity,
    Authority,
    SYMBOLIC_DOMAINS,
    transfer_ceiling_for_evidence,
)
from .schema import AIONPattern, AIONInstance, AIONMapping, AIONContract
from .decision import Verdict, Decision
from .classifier import EvidenceClassifier
from .transfer_gate import AnalogyTransferGate
from .promotion_gate import PromotionGate
from .contradiction_scan import ContradictionScanner, Contradiction
from .provenance import ProvenanceStore
from . import envelope

__all__ = [
    "EvidenceLevel", "TransferLevel", "RiskClass", "TrustState", "Sensitivity",
    "Authority", "SYMBOLIC_DOMAINS", "transfer_ceiling_for_evidence",
    "AIONPattern", "AIONInstance", "AIONMapping", "AIONContract",
    "Verdict", "Decision", "EvidenceClassifier", "AnalogyTransferGate",
    "PromotionGate", "ContradictionScanner", "Contradiction", "ProvenanceStore",
    "envelope",
]

"""Urbi Dream Layer (ΦΔ) — offline replay, consolidation, and coherence repair.

The DREAM consumer of PredictionRecords. Audit-only, no world action, CORE-write-free.
Discharges Axiom 11 (compression preserves structure) and surfaces Axiom 12
(self-confirmation) via the Simulacrum detector.
"""
from ai_chi.urbi.dream.records import (
    ConsolidationAction, ContradictionKind, Contradiction,
    ConsolidationProposal, DreamCycleReport, ACTION_TARGET_TIER,
)
from ai_chi.urbi.dream.replay import DreamReplayEngine, prediction_record_from_payload
from ai_chi.urbi.dream.contradiction import ContradictionEngine
from ai_chi.urbi.dream.consolidation import ConsolidationEngine
from ai_chi.urbi.dream.lens import DreamLens, NullDreamLens, OllamaDreamLens, sanitize_dream_lens_hints
from ai_chi.urbi.dream.engine import DreamConsolidator, COH_EXIT
from ai_chi.urbi.dream.scheduler import DreamScheduler
from ai_chi.urbi.dream.auditor import (
    DreamReplayAuditor, SIGMA_DREAM, COHERENCE_EXIT_THRESHOLD,
)

__all__ = [
    "ConsolidationAction", "ContradictionKind", "Contradiction",
    "ConsolidationProposal", "DreamCycleReport", "ACTION_TARGET_TIER",
    "DreamReplayEngine", "ContradictionEngine", "ConsolidationEngine",
    "DreamLens", "NullDreamLens", "OllamaDreamLens", "sanitize_dream_lens_hints",
    "DreamReplayAuditor", "SIGMA_DREAM", "COHERENCE_EXIT_THRESHOLD",
    "DreamConsolidator", "COH_EXIT", "DreamScheduler", "prediction_record_from_payload",
]

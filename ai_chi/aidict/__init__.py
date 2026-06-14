"""AIDICT — A.I. Development Investigation Contract Tracker.

A local-first scientific evidence/claim ledger. NOT a new system: it is the
existing P0 Reality Loop pointed at a new sensor stream — the AI-development web
(papers, repos, model cards, podcasts, social text) instead of maritime telemetry.

Design law (from AIDICT.txt):
  * Social/transcript data is **signal, not truth**. Noise is classified, not discarded.
  * Confidence = **extraction** confidence, not truth confidence.
  * The LLM is an **extractor only**, never an authority.
  * Every claim becomes an **investigation contract**: what evidence would
    validate or contradict it, and what future condition can be tested.

Integration (reuse, do not fork):
  * Claims ride the membrane as ``ext.claim`` (ext.* universal carrier).
  * Contracts/patterns/tasks are cognition (``m.*``) — never action, so Ω₈ never
    suppresses them; they flow in WAKE/LIMINAL/DREAM alike.
  * Claims route through the **live Urbi 3-6-9 auditor** via the existing bridge.
  * Suspended ``[=]`` verdicts become ``m.prediction_record`` → ΦΔ dream layer.
  * Outcomes/validation feed the existing CAL/Ω₄ calibration monitor.

GPLv3 · offline-first · CM5 + Hailo-10H ready.
"""
from __future__ import annotations

from ai_chi.aidict.schemas import (
    SourceRecord,
    ClaimRecord,
    EvidenceRecord,
    ContractRecord,
    PatternRecord,
    PredictionRecord,
    ValidationRecord,
    VerificationTask,
    SIGMA_CLAIM,
    SIGMA_CONTRACT,
    SIGMA_PATTERN,
    SIGMA_VERIFICATION,
    SIGMA_VALIDATION,
)
from ai_chi.aidict.scout import AidictScout, ScoutReport

__all__ = [
    "SourceRecord",
    "ClaimRecord",
    "EvidenceRecord",
    "ContractRecord",
    "PatternRecord",
    "PredictionRecord",
    "ValidationRecord",
    "VerificationTask",
    "AidictScout",
    "ScoutReport",
    "SIGMA_CLAIM",
    "SIGMA_CONTRACT",
    "SIGMA_PATTERN",
    "SIGMA_VERIFICATION",
    "SIGMA_VALIDATION",
]

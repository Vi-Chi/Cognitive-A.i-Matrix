"""AIDICT record stack + M-protocol σ-class mapping.

Each record is a plain dataclass with a stable id, a ``to_payload()`` (the dict
that rides inside π), and a ``to_message()`` that wraps it in a validated
canonical ``MMessage``. The σ-class for each record is chosen so the membrane's
existing invariants do the right thing:

    SourceRecord       -> (metadata; carried inside claim/contract payloads)
    ClaimRecord        -> ext.claim            (universal carrier; raw signal)
    EvidenceRecord     -> m.evidence           (reuses the existing evidence class)
    ContractRecord     -> m.contract           (cognition: the audit primitive)
    PatternRecord      -> m.pattern            (cognition: detected structure)
    PredictionRecord   -> m.prediction_record  (the canonical mebus record; reused)
    ValidationRecord   -> m.validation         (cognition: later evidence resolving a contract)
    VerificationTask   -> m.verification_task  (cognition checklist item — NOT action)

None of the new σ values are action-class (they are not in
ACTION_LAYER_SIGNATURES and carry no ``cmd.`` prefix), so Ω₈ never suppresses
them — auditing/evidence must keep flowing in DREAM.

``confidence`` everywhere means *extraction* confidence: "how sure am I the
source made this claim", never "how true the claim is".
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from ai_chi.bus import MMessage, Mode

# --- σ-class registry (the contract between AIDICT and the membrane) ---------
SIGMA_SOURCE = "ext.source"
SIGMA_SEGMENT = "ext.segment"
SIGMA_CLAIM = "ext.claim"
SIGMA_EVIDENCE = "m.evidence"
SIGMA_CONTRACT = "m.contract"
SIGMA_PATTERN = "m.pattern"
SIGMA_PREDICTION = "m.prediction_record"
SIGMA_VALIDATION = "m.validation"
SIGMA_VERIFICATION = "m.verification_task"

DEFAULT_DOMAIN = "aidict.observatory"
DEFAULT_DEST = "urbi"


def _short_hash(*parts: Any) -> str:
    blob = "|".join(str(p) for p in parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def _ctx(confidence: float, provenance: list[str], domain: str = DEFAULT_DOMAIN) -> dict:
    """κ envelope: trust_score carries *extraction* confidence (sensor trust)."""
    return {
        "trust_score": max(0.0, min(1.0, float(confidence))),
        "domain": domain,
        "provenance": list(provenance),
    }


# ---------------------------------------------------------------------------
@dataclass
class SourceRecord:
    """Who / where / when. Provenance root for every downstream record."""

    source_type: str
    source_name: str = ""
    source_url: str = ""
    author_or_channel: str = ""
    published_at: str = ""
    collected_at: str = ""
    acquisition_method: str = "manual"  # manual|jdownloader|yt_dlp|api|rss|copy_paste|unknown
    language: str = ""
    caption_type: str = "unknown"       # manual|auto|unknown
    file_hash: str = ""
    quality_notes: str = ""
    confidence: float = 0.9
    source_id: str = ""

    def __post_init__(self) -> None:
        if not self.source_id:
            self.source_id = "src_" + _short_hash(
                self.source_type, self.source_name, self.source_url, self.file_hash
            )

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "SourceRecord"
        return d

    @property
    def provenance_uri(self) -> str:
        return self.source_url or f"urn:aidict:{self.acquisition_method}:{self.source_id}"

    def to_message(self, *, destination: str = DEFAULT_DEST, mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(
            sigma=SIGMA_SOURCE,
            payload=self.to_payload(),
            destination=destination,
            context=_ctx(self.confidence, [self.provenance_uri, "aidict_scout"]),
            mode=mode,
        ).validate()


@dataclass
class SegmentRecord:
    """A bounded, timestamped span of a source — the bridge from raw text to claims.

    Makes every EvidenceRecord/ClaimRecord traceable to an exact subtitle/transcript
    span (feedback correction: provenance must reach the span, not just the source).
    """

    source_id: str
    text: str
    timestamp_start: str = ""
    timestamp_end: str = ""
    speaker: str = "unknown"
    index: int = 0
    quality_flags: list[str] = field(default_factory=list)
    segment_id: str = ""

    def __post_init__(self) -> None:
        if not self.segment_id:
            self.segment_id = "seg_" + _short_hash(self.source_id, self.index, self.text[:40])

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "SegmentRecord"
        return d

    def to_message(self, *, destination: str = DEFAULT_DEST, mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(
            sigma=SIGMA_SEGMENT,
            payload=self.to_payload(),
            destination=destination,
            context=_ctx(0.9, [self.source_id, "aidict_scout"]),
            mode=mode,
        ).validate()


@dataclass
class ClaimRecord:
    """What was claimed, with the evidence span that supports the extraction."""

    source_id: str
    claim_text: str
    segment_id: str = ""
    normalized_claim: str = ""
    claim_type: str = "opinion"
    entities: list[str] = field(default_factory=list)
    evidence_span: str = ""
    hype_markers: list[str] = field(default_factory=list)
    timestamp_start: str = ""
    timestamp_end: str = ""
    confidence: float = 0.0       # extraction confidence
    verification_required: bool = True
    provenance_uri: str = ""
    claim_id: str = ""

    def __post_init__(self) -> None:
        if not self.normalized_claim:
            self.normalized_claim = self.claim_text
        if not self.evidence_span:
            self.evidence_span = self.claim_text
        if not self.claim_id:
            self.claim_id = "claim_" + _short_hash(
                self.source_id, self.evidence_span, self.timestamp_start
            )

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "ClaimRecord"
        return d

    def to_message(self, *, destination: str = DEFAULT_DEST, mode: Mode = Mode.WAKE) -> MMessage:
        prov = [self.provenance_uri or self.source_id, "aidict_scout"]
        payload = self.to_payload()
        # Mirror the ManualTextObserver shape so Φ_AGG / Urbi intake read raw_data.
        payload["raw_data"] = self.claim_text
        payload["source_type"] = "aidict_claim"
        payload["sensor_confidence"] = self.confidence
        return MMessage(
            sigma=SIGMA_CLAIM,
            payload=payload,
            destination=destination,
            context=_ctx(self.confidence, prov),
            mode=mode,
        ).validate()


@dataclass
class EvidenceRecord:
    """A source span that supports (or weakens) a claim."""

    claim_id: str
    source_id: str
    span: str
    locator: str = ""              # timestamp / line / url fragment
    supports: bool = True
    confidence: float = 0.0
    evidence_id: str = ""

    def __post_init__(self) -> None:
        if not self.evidence_id:
            self.evidence_id = "ev_" + _short_hash(self.claim_id, self.span, self.locator)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "EvidenceRecord"
        return d

    def to_message(self, *, destination: str = DEFAULT_DEST, mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(
            sigma=SIGMA_EVIDENCE,
            payload=self.to_payload(),
            destination=destination,
            context=_ctx(self.confidence, [self.source_id, "aidict_scout"]),
            mode=mode,
        ).validate()


@dataclass
class VerificationTask:
    """A primary-source check that would help satisfy a contract. NOT actuation."""

    claim_id: str
    task_type: str                 # check_github|check_arxiv|check_huggingface|check_license|...
    query: str
    reason: str = ""
    priority: str = "medium"       # low|medium|high|critical
    status: str = "pending"
    task_id: str = ""

    def __post_init__(self) -> None:
        if not self.task_id:
            self.task_id = "verify_" + _short_hash(self.claim_id, self.task_type, self.query)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "VerificationTask"
        return d

    def to_message(self, *, destination: str = DEFAULT_DEST, mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(
            sigma=SIGMA_VERIFICATION,
            payload=self.to_payload(),
            destination=destination,
            context=_ctx(0.8, [self.claim_id, "aidict_scout"]),
            mode=mode,
        ).validate()


@dataclass
class ContractRecord:
    """The central primitive: what must be checked for a claim to be validated.

    Status lifecycle: open -> partially_satisfied -> satisfied | contradicted |
    expired. ``risk_level`` and ``learning_value`` feed Autopoiesis curiosity
    budgeting (high-learning_value contracts are prioritised).
    """

    claim_id: str
    contract_type: str             # benchmark_validation|license_validation|release_validation|...
    validation_requirements: list[str] = field(default_factory=list)
    required_evidence: list[str] = field(default_factory=list)
    verification_task_ids: list[str] = field(default_factory=list)
    current_status: str = "open"   # EVIDENCE-driven: open->partially_satisfied->satisfied|contradicted|expired
    risk_level: str = "medium"     # low|medium|high|critical
    learning_value: float = 0.5
    audit_verdict: str = ""        # raw "+" | "-" | "=" | "" (from Urbi, if audited)
    audit_signal: str = "pending"  # attached signal: audit_support_signal|audit_contradiction_signal|audit_suspended|pending
    audit_reason: str = ""
    audit_required: bool = True
    contract_id: str = ""

    def __post_init__(self) -> None:
        if not self.contract_id:
            self.contract_id = "contract_" + _short_hash(self.claim_id, self.contract_type)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "ContractRecord"
        return d

    def to_message(self, *, destination: str = DEFAULT_DEST, mode: Mode = Mode.WAKE) -> MMessage:
        # trust_score here reflects how settled the contract is, not claim truth.
        settled = {"satisfied": 0.95, "contradicted": 0.9, "partially_satisfied": 0.5,
                   "expired": 0.3, "open": 0.2}.get(self.current_status, 0.2)
        return MMessage(
            sigma=SIGMA_CONTRACT,
            payload=self.to_payload(),
            destination=destination,
            context=_ctx(settled, [self.claim_id, "aidict_contract"]),
            mode=mode,
        ).validate()


@dataclass
class PatternRecord:
    """A recurring structure across claims (repeated/hype_wave/contradiction/cooccurrence)."""

    pattern_type: str
    pattern_name: str
    description: str = ""
    linked_claims: list[str] = field(default_factory=list)
    linked_entities: list[str] = field(default_factory=list)
    novelty_score: float = 0.0
    hype_score: float = 0.0
    evidence_strength: float = 0.0
    audit_required: bool = True
    pattern_id: str = ""

    def __post_init__(self) -> None:
        if not self.pattern_id:
            self.pattern_id = "pat_" + _short_hash(self.pattern_type, self.pattern_name)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "PatternRecord"
        return d

    def to_message(self, *, destination: str = DEFAULT_DEST, mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(
            sigma=SIGMA_PATTERN,
            payload=self.to_payload(),
            destination=destination,
            context=_ctx(self.evidence_strength, ["aidict_pattern_engine"]),
            mode=mode,
        ).validate()


@dataclass
class PredictionRecord:
    """A future-facing, measurable statement extracted from a source.

    Distinct from mebus.PredictionRecord (the dream-synapse record). This is the
    AIDICT *extraction* of a prediction in the wild; it can later be promoted to
    a mebus PredictionRecord when wired to CAL/Ω₄.
    """

    source_id: str
    speaker_or_author: str
    prediction_text: str
    target_date_or_window: str = ""
    measurable_condition: str = ""
    linked_claims: list[str] = field(default_factory=list)
    status: str = "pending"        # pending|fulfilled|failed|expired|unmeasurable
    confidence: float = 0.0
    prediction_id: str = ""

    def __post_init__(self) -> None:
        if not self.prediction_id:
            self.prediction_id = "pred_" + _short_hash(self.source_id, self.prediction_text)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "AidictPredictionRecord"
        return d

    def to_message(self, *, destination: str = "cal", mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(
            sigma=SIGMA_PREDICTION,
            payload=self.to_payload(),
            destination=destination,
            context=_ctx(self.confidence, [self.source_id, "aidict_scout"]),
            mode=mode,
        ).validate()


@dataclass
class ValidationRecord:
    """Later evidence that supports, weakens, or contradicts a contract."""

    contract_id: str
    claim_id: str
    outcome: str                   # supports|weakens|contradicts|inconclusive
    evidence_ids: list[str] = field(default_factory=list)
    note: str = ""
    confidence: float = 0.0
    validation_id: str = ""

    def __post_init__(self) -> None:
        if not self.validation_id:
            self.validation_id = "val_" + _short_hash(self.contract_id, self.outcome, self.note)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "ValidationRecord"
        return d

    def to_message(self, *, destination: str = DEFAULT_DEST, mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(
            sigma=SIGMA_VALIDATION,
            payload=self.to_payload(),
            destination=destination,
            context=_ctx(self.confidence, [self.contract_id, "aidict_validation"]),
            mode=mode,
        ).validate()

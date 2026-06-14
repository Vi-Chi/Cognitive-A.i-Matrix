"""AION record schemas: Pattern, Instance, Mapping, Contract.

Stdlib dataclasses with strict enums and round-trip (to_dict/from_dict)
serialization. from_dict rejects unknown fields (defence against drifted /
hallucinated exports — sandbox content is evidence, not truth).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, fields, asdict
from typing import Any, Optional

from .ontology import (
    EvidenceLevel, TransferLevel, RiskClass, TrustState, Sensitivity, Authority,
)


def _now() -> float:
    return time.time()


def _enum_in(enum_cls, value):
    """Coerce a stored value (name, value, or instance) into an enum member."""
    if isinstance(value, enum_cls):
        return value
    # IntEnum by int
    try:
        return enum_cls(value)
    except (ValueError, KeyError):
        pass
    if isinstance(value, str):
        # by name (e.g. "T4", "CAUSAL", "HIGH")
        try:
            return enum_cls[value]
        except KeyError:
            pass
    raise ValueError(f"{value!r} is not a valid {enum_cls.__name__}")


def _enum_out(value):
    """Serialize an enum to a stable scalar (IntEnum -> int, Enum -> value)."""
    if isinstance(value, (EvidenceLevel, TransferLevel)):
        return int(value)
    if isinstance(value, (RiskClass, TrustState, Sensitivity, Authority)):
        return value.value
    return value


def _strict_keys(cls, data: dict) -> None:
    allowed = {f.name for f in fields(cls)}
    extra = set(data) - allowed
    if extra:
        raise ValueError(f"{cls.__name__}: unknown fields rejected: {sorted(extra)}")


@dataclass
class AIONPattern:
    """A recurring structure/mechanism observed in one or more domains."""
    id: str
    name: str
    archetype: str = ""
    domains: list = field(default_factory=list)
    description: str = ""
    structural_features: list = field(default_factory=list)
    causal_mechanism: Optional[str] = None
    evidence_level: EvidenceLevel = EvidenceLevel.RESEMBLANCE
    transfer_level: TransferLevel = TransferLevel.T0
    risk_class: RiskClass = RiskClass.LOW
    trust_state: TrustState = TrustState.EQUALS
    # delta (provenance)
    source_refs: list = field(default_factory=list)
    source_hashes: list = field(default_factory=list)
    contradiction_refs: list = field(default_factory=list)
    # kappa
    confidence: float = 0.0
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    origin_authority: Authority = Authority.UNKNOWN
    action_allowed: bool = False
    # tau
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)
    causal_parent: Optional[str] = None

    def __post_init__(self):
        self.evidence_level = _enum_in(EvidenceLevel, self.evidence_level)
        self.transfer_level = _enum_in(TransferLevel, self.transfer_level)
        self.risk_class = _enum_in(RiskClass, self.risk_class)
        self.trust_state = _enum_in(TrustState, self.trust_state)
        self.sensitivity = _enum_in(Sensitivity, self.sensitivity)
        self.origin_authority = _enum_in(Authority, self.origin_authority)
        if not self.id or not self.name:
            raise ValueError("AIONPattern requires id and name")

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("evidence_level", "transfer_level", "risk_class",
                  "trust_state", "sensitivity", "origin_authority"):
            d[k] = _enum_out(getattr(self, k))
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "AIONPattern":
        _strict_keys(cls, data)
        return cls(**data)


@dataclass
class AIONInstance:
    """A concrete observation of a pattern in a domain."""
    id: str
    pattern_id: str
    domain: str
    observed_at: float = field(default_factory=_now)
    evidence_ref: Optional[str] = None
    submitted_by: Authority = Authority.UNKNOWN
    notes: str = ""

    def __post_init__(self):
        self.submitted_by = _enum_in(Authority, self.submitted_by)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["submitted_by"] = _enum_out(self.submitted_by)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "AIONInstance":
        _strict_keys(cls, data)
        return cls(**data)


@dataclass
class AIONMapping:
    """A proposed transfer of a pattern from one domain to another."""
    id: str
    pattern_id: str
    source_domain: str
    target_domain: str
    transfer_level: TransferLevel = TransferLevel.T0
    rationale: str = ""
    approved: bool = False

    def __post_init__(self):
        self.transfer_level = _enum_in(TransferLevel, self.transfer_level)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["transfer_level"] = _enum_out(self.transfer_level)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "AIONMapping":
        _strict_keys(cls, data)
        return cls(**data)


@dataclass
class AIONContract:
    """MΣBUS-gated allowed/forbidden-use wrapper for an approved pattern."""
    id: str
    pattern_id: str
    allowed_use: list = field(default_factory=list)
    forbidden_use: list = field(default_factory=list)
    target_module: str = ""
    required_evidence_level: EvidenceLevel = EvidenceLevel.ENGINEERING
    required_transfer_level: TransferLevel = TransferLevel.T4
    rollback_path: Optional[str] = None
    audits_required: list = field(default_factory=lambda: ["urbi"])
    simulations_required: list = field(default_factory=lambda: ["dream"])
    promotion_records: list = field(default_factory=list)
    risk_class: RiskClass = RiskClass.MEDIUM
    human_approval_required: bool = False
    world_action_allowed: bool = False
    proposed_at: float = field(default_factory=_now)
    approved_at: Optional[float] = None
    expires_at: Optional[float] = None

    def __post_init__(self):
        self.required_evidence_level = _enum_in(EvidenceLevel, self.required_evidence_level)
        self.required_transfer_level = _enum_in(TransferLevel, self.required_transfer_level)
        self.risk_class = _enum_in(RiskClass, self.risk_class)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["required_evidence_level"] = _enum_out(self.required_evidence_level)
        d["required_transfer_level"] = _enum_out(self.required_transfer_level)
        d["risk_class"] = _enum_out(self.risk_class)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "AIONContract":
        _strict_keys(cls, data)
        return cls(**data)

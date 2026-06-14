"""UrbiAuditSignal — the single proof-carrying object every Urbi verdict emits.

Canonical schema from URBI_369_FUNDAMENTAL_CORE §11.2. Hard invariant: action_allowed
is always False (Urbi judges/scores/vetoes; it never grants action). The signal
reduces to the PolicyGate's audit-signal contract (`to_gate_signal`) and to a mebus
PredictionRecord (`to_prediction_record`) — one proof bundle, two consumers.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

VALID_EPISTEMIC_STATES = {"[+]", "[-]", "[=]"}

# Gate-signal contract — MIRRORS ai_chi.orbi.policy_gate's SUPPORT/CONTRADICTION/
# SUSPENDED/PENDING. Urbi must not import Orbi (dependency direction / separation of
# powers), so the contract is duplicated here and asserted equal to the gate's in tests.
GATE_SUPPORT = "audit_support_signal"
GATE_CONTRADICTION = "audit_contradiction_signal"
GATE_SUSPENDED = "audit_suspended"
GATE_PENDING = "pending"

_CONSTITUTIONAL_CODES = {
    "urbi_non_actuation_violation",
    "invalid_trust_state",
    "model_attempted_direct_permission",
    "mebus_cannot_judge",
    "orbi_cannot_judge_itself",
}


class AuditSignalError(ValueError):
    pass


@dataclass
class UrbiAuditSignal:
    claim_id: str
    epistemic_state: str
    truth_score: float = 0.0
    integrity_score: float = 0.0
    coherence_score: float = 0.0
    audit_state: int = 0
    reason_code: str = ""
    constitutional_violations: list = field(default_factory=list)
    required_evidence: list = field(default_factory=list)
    next_observation_request: list = field(default_factory=list)
    contradictions: list = field(default_factory=list)
    evidence_gaps: list = field(default_factory=list)
    falsification_tests: list = field(default_factory=list)
    causal_parents: list = field(default_factory=list)
    record_type: str = "UrbiAuditSignal"
    version: str = "0.1"
    action_allowed: bool = False

    def __post_init__(self):
        self.action_allowed = False
        if self.epistemic_state not in VALID_EPISTEMIC_STATES:
            raise AuditSignalError(
                f"epistemic_state {self.epistemic_state!r} not in {sorted(VALID_EPISTEMIC_STATES)}")
        self.audit_state = max(0, min(9, int(self.audit_state)))
        for s in ("truth_score", "integrity_score", "coherence_score"):
            setattr(self, s, max(0.0, min(1.0, float(getattr(self, s)))))

    # ---- producers ----
    @classmethod
    def from_audit_result(cls, res) -> "UrbiAuditSignal":
        contradictions = list(getattr(res, "contradictions", []))
        violations = [c for c in contradictions if c in _CONSTITUTIONAL_CODES]
        return cls(
            claim_id=res.record_id, epistemic_state=res.epistemic_state,
            truth_score=res.truth_score, integrity_score=res.integrity_score,
            coherence_score=res.coherence_score, audit_state=res.audit_state,
            reason_code=res.reason_code, constitutional_violations=violations,
            required_evidence=list(getattr(res, "required_evidence", [])),
            next_observation_request=list(getattr(res, "next_observations", [])),
            contradictions=contradictions,
            evidence_gaps=list(getattr(res, "evidence_gaps", [])),
            falsification_tests=list(getattr(res, "falsification_tests", [])),
            causal_parents=list(getattr(res, "provenance_delta", [])),
        )

    @classmethod
    def from_validated(cls, sanitized: dict, *, claim_id: Optional[str] = None) -> "UrbiAuditSignal":
        return cls(
            claim_id=claim_id or str(sanitized.get("claim_id", "urbi_lens")),
            epistemic_state=sanitized.get("epistemic_state", "[=]"),
            truth_score=float(sanitized.get("truth_score", 0.0)),
            integrity_score=float(sanitized.get("integrity_score", 0.0)),
            coherence_score=float(sanitized.get("coherence_score", 0.0)),
            audit_state=int(sanitized.get("audit_state", 0)),
            reason_code=str(sanitized.get("reason_code", "")),
            constitutional_violations=list(sanitized.get("constitutional_violations", [])),
            required_evidence=list(sanitized.get("required_evidence", []))
            or list(sanitized.get("audit_warnings", [])),
            next_observation_request=list(sanitized.get("next_observation_request", [])),
            causal_parents=list(sanitized.get("provenance_refs", [])),
        )

    # ---- consumers ----
    @property
    def has_constitutional_violation(self) -> bool:
        return bool(self.constitutional_violations)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["action_allowed"] = False
        return d

    def to_gate_signal(self) -> str:
        """Reduce this proof bundle to the PolicyGate's audit-signal contract.

        A constitutional violation ALWAYS reduces to CONTRADICTION (deny), even if
        the epistemic state were [+]. Then [+]->SUPPORT, [-]->CONTRADICTION,
        [=]->SUSPENDED, else PENDING (fail-safe).
        """
        if self.has_constitutional_violation:
            return GATE_CONTRADICTION
        return {"[+]": GATE_SUPPORT, "[-]": GATE_CONTRADICTION,
                "[=]": GATE_SUSPENDED}.get(self.epistemic_state, GATE_PENDING)

    def to_prediction_record(self, *, domain: str = "urbi.audit", mode=None):
        from mebus import PredictionRecord, Mode  # lazy
        return PredictionRecord(
            record_id=self.claim_id, belief_state=self.to_dict(),
            predicted_outcome={"action_allowed": False, "epistemic_state": self.epistemic_state,
                               "audit_state": self.audit_state},
            domain=domain, mu_at_time=mode or Mode.WAKE,
            confidence=self.integrity_score, causal_parents=list(self.causal_parents),
        )

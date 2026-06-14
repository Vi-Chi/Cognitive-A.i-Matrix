"""Urbi 3-6-9 deterministic audit kernel.

Harvested + hardened from the Grok prototype (urbi/promoter/audit_hooks.py),
DECOUPLED from MemoryStore: it operates on a plain AuditInput so it runs
standalone and pairs directly with AION patterns (an AIONPattern maps cleanly
onto an AuditInput).

3 — observe   : provenance, payload, context, confidence.
6 — model     : contradictions + evidence gaps + corruption modes.
9 — predict   : integrity / truth / coherence scores -> epistemic state + recommendation.

Urbi invariant: the result ALWAYS has action_allowed = False. Urbi emits audit
cognition only; it never executes, grants, or writes world state.
Stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuditInput:
    """Minimal record under audit (decoupled from any store)."""
    id: str
    payload: dict = field(default_factory=dict)
    provenance: list = field(default_factory=list)
    kappa: float = 0.0
    trust_state: str = "="
    sensitivity: str = "public"
    tau: int = 0
    context: dict = field(default_factory=dict)


@dataclass(frozen=True)
class AuditResult:
    record_id: str
    epistemic_state: str          # [+] / [-] / [=]
    integrity_score: float
    truth_score: float
    coherence_score: float
    audit_state: int              # 3 plausible / 5 cross-supported / 6 contradiction
    action_allowed: bool          # ALWAYS False (Urbi invariant)
    reason_code: str
    contradictions: list
    evidence_gaps: list
    falsification_tests: list
    required_evidence: list
    next_observations: list
    provenance_delta: list
    audit_tau: int

    @property
    def trust_verdict(self) -> str:
        return self.epistemic_state.strip("[]")

    @property
    def recommendation(self) -> str:
        return {"+": "promote_core", "-": "negative"}.get(self.trust_verdict, "suspended")

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)


class Urbi369Audit:
    """Deterministic 3-6-9 integrity kernel. No store, no action, no mutation."""

    def run(self, rec: AuditInput, context: dict | None = None) -> AuditResult:
        context = context or rec.context or {}
        obs = self._observe(rec, context)
        contradictions, gaps = self._model(rec, obs)
        scores, verdict, state = self._predict(rec, contradictions, gaps)
        return AuditResult(
            record_id=rec.id,
            epistemic_state=f"[{verdict}]",
            integrity_score=scores["integrity"],
            truth_score=scores["truth"],
            coherence_score=scores["coherence"],
            audit_state=state,
            action_allowed=False,  # invariant
            reason_code=self._reason_code(verdict, contradictions, gaps),
            contradictions=contradictions,
            evidence_gaps=gaps,
            falsification_tests=self._falsification(rec),
            required_evidence=self._missing_evidence(gaps),
            next_observations=["continue_tracking", "log_for_dream_replay",
                               "preserve_divergent_outliers"],
            provenance_delta=[f"urbi:369:{rec.id}"],
            audit_tau=rec.tau + 1,
        )

    # 3 — observe
    def _observe(self, rec: AuditInput, context: dict) -> dict:
        return {
            "provenance_len": len(rec.provenance),
            "kappa": rec.kappa,
            "payload_keys": set(rec.payload.keys()),
            "sensitivity": rec.sensitivity,
            "context": context,
        }

    # 6 — model contradictions + gaps
    def _model(self, rec: AuditInput, obs: dict):
        contradictions, gaps = [], []
        keys = obs["payload_keys"]
        if obs["provenance_len"] < 2:
            gaps.append("weak_provenance")
        if rec.kappa < 0.75:
            gaps.append("low_kappa")
        risk = str(rec.payload.get("risk", "")).lower()
        if risk in {"high", "critical"} and not rec.payload.get("urbi_signal"):
            contradictions.append("high_risk_without_urbi_signal")
        # Urbi may never write world state (separation of powers).
        if rec.payload.get("writes_world_state") and str(rec.payload.get("source", "")).lower() == "urbi":
            contradictions.append("urbi_non_actuation_violation")
        if "claim" in keys and not ("evidence" in keys or rec.payload.get("evidence")):
            gaps.append("claim_without_evidence")
        if rec.trust_state not in {"+", "-", "=", "[+]", "[-]", "[=]"}:
            contradictions.append("invalid_trust_state")
        return contradictions, gaps

    # 9 — predict / score
    def _predict(self, rec: AuditInput, contradictions: list, gaps: list):
        clamp = lambda x: max(0.0, min(1.0, x))
        integrity = clamp(rec.kappa - 0.25 * len(contradictions) - 0.10 * len(gaps))
        truth = clamp(integrity * 0.85)
        coherence = clamp(1.0 - 0.30 * len(gaps) - 0.40 * len(contradictions))
        scores = {"integrity": integrity, "truth": truth, "coherence": coherence}
        if contradictions:
            return scores, "-", 6
        if not gaps and rec.kappa >= 0.85 and len(rec.provenance) >= 2:
            return scores, "+", 5
        return scores, "=", 3

    def _falsification(self, rec: AuditInput) -> list:
        base = [f"cross_verify:{p}" for p in rec.provenance[:3]]
        return base or ["seek_independent_source"]

    def _missing_evidence(self, gaps: list) -> list:
        req = []
        if "weak_provenance" in gaps:
            req.append("second_independent_provenance_source")
        if "low_kappa" in gaps:
            req.append("confidence_calibration_record")
        if "claim_without_evidence" in gaps:
            req.append("supporting_evidence_payload")
        return req or ["maintain_periodic_revalidation"]

    def _reason_code(self, verdict: str, contradictions: list, gaps: list) -> str:
        if contradictions:
            return "contradiction_detected"
        if gaps:
            return "insufficient_cross_support"
        return "cross_supported" if verdict == "+" else "suspended"

"""Urbi deterministic Core Validator — "the Lens proposes; the Core disposes".

Harvested + hardened from the Google AI Studio prototype (aicore_proto/urbi.py).
A generative Urbi Lens (an LLM) may emit a candidate audit-signal JSON. This
module sanitizes it deterministically: no model string is an action permit.

Hardening added over the prototype:
  * action_allowed is stripped from ANY non-urbi verdict authority, not only when
    it is literally True (defence against truthy values / authority spoofing).
  * cloud/chain/omni origins can never carry action authority (evidence-only).
  * a typed UrbiAuditSignal wrapper with a stable to_dict().
  * the input record is never mutated (always operates on a copy).

Stdlib only. No realm dependency (safe to land without constitutional sign-off).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

VALID_EPISTEMIC_STATES = {"[+]", "[-]", "[=]"}

# Origins that may submit evidence but never carry action authority.
_EVIDENCE_ONLY_ORIGINS = {"cloud", "chain", "omni", "external", "lens", "model"}
# Only Urbi may originate an audit verdict.
_VERDICT_AUTHORITY = "urbi"


def force_veto(record: dict[str, Any], reason: str) -> None:
    """Hard negative: set [-], block action, log a constitutional violation."""
    record["action_allowed"] = False
    record["epistemic_state"] = "[-]"
    record.setdefault("constitutional_violations", []).append(reason)


def preserve_uncertainty(record: dict[str, Any], reason: str) -> None:
    """Suspend to [=]: the safety-preserving state. Block action, log a warning."""
    record["action_allowed"] = False
    record["epistemic_state"] = "[=]"
    record.setdefault("audit_warnings", []).append(reason)


def validate_urbi_audit_signal(record: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a candidate audit-signal dict emitted by a generative Urbi Lens.

    Returns a NEW dict; the input is never mutated. Resulting dict always has
    action_allowed == False unless an explicit, separately-gated grant exists
    outside this layer (this layer never grants).
    """
    sanitized = dict(record)

    # 1. Epistemic state must be one of the tri-state values.
    if sanitized.get("epistemic_state") not in VALID_EPISTEMIC_STATES:
        force_veto(sanitized, "invalid_epistemic_state")

    # 2. A generative layer may never grant permission. Strip ANY truthy
    #    action_allowed, and any verdict not authored by urbi authority.
    authority = str(sanitized.get("verdict_authority", "")).lower()
    if sanitized.get("action_allowed"):
        sanitized["action_allowed"] = False
        sanitized.setdefault("constitutional_violations", []).append(
            "model_attempted_direct_permission"
        )
    if authority and authority != _VERDICT_AUTHORITY:
        sanitized.setdefault("constitutional_violations", []).append(
            f"non_urbi_verdict_authority:{authority}"
        )
        sanitized["action_allowed"] = False

    # 3. Evidence-only origins can never carry action authority.
    origin = str(sanitized.get("origin", "")).lower()
    if origin in _EVIDENCE_ONLY_ORIGINS:
        sanitized["action_allowed"] = False
        sanitized["origin_effect"] = f"{origin}_is_evidence_only"

    # 4. Action without provenance degrades trust to suspended.
    if not sanitized.get("provenance_refs"):
        preserve_uncertainty(
            sanitized, "missing_provenance_trace_degrading_trust_to_suspended"
        )

    # 5. DREAM mode suppresses action (Ω₈).
    if str(sanitized.get("mode_mu", "")).upper() == "DREAM":
        sanitized["action_allowed"] = False
        sanitized["mode_effect"] = "dream_mode_suppresses_action"

    # 6. Unresolved contradictions mandate a holding pattern.
    if sanitized.get("contradiction_flags"):
        preserve_uncertainty(
            sanitized, "unresolved_contradictions_mandate_holding_pattern"
        )

    # Final invariant: this layer never emits an actionable verdict.
    sanitized["action_allowed"] = bool(sanitized.get("action_allowed", False)) and False
    return sanitized


@dataclass
class UrbiAuditSignal:
    """Typed convenience wrapper around the sanitized signal dict."""
    epistemic_state: str
    action_allowed: bool = False
    provenance_refs: list = field(default_factory=list)
    constitutional_violations: list = field(default_factory=list)
    audit_warnings: list = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_lens(cls, record: dict[str, Any]) -> "UrbiAuditSignal":
        s = validate_urbi_audit_signal(record)
        known = {"epistemic_state", "action_allowed", "provenance_refs",
                 "constitutional_violations", "audit_warnings"}
        return cls(
            epistemic_state=s.get("epistemic_state", "[=]"),
            action_allowed=False,  # invariant
            provenance_refs=list(s.get("provenance_refs", [])),
            constitutional_violations=list(s.get("constitutional_violations", [])),
            audit_warnings=list(s.get("audit_warnings", [])),
            extra={k: v for k, v in s.items() if k not in known},
        )

    def to_dict(self) -> dict:
        d = {
            "epistemic_state": self.epistemic_state,
            "action_allowed": False,
            "provenance_refs": list(self.provenance_refs),
            "constitutional_violations": list(self.constitutional_violations),
            "audit_warnings": list(self.audit_warnings),
        }
        d.update(self.extra)
        return d

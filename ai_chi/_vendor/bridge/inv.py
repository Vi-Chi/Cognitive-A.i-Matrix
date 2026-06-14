"""INV — Invariant gate for the Urbi emit path (minimal P0 enforcement).

The reconciled Ω-registry (Ω₁–Ω₈) spans the whole system. This gate enforces only the
invariants meaningful at the moment Urbi emits a belief onto MΣBUS; the rest are declared
here for traceability and owned by other components (not silently assumed).

Enforced here:
  Ω₆  natural language ∉ core   — the canonical value must be a structured payload.
  Ω₇  provenance / causal log   — every emission carries provenance or causal parents.
  Urbi-non-actuation            — Urbi audits, never acts (3-6-9 out-of-loop); it may
                                  never emit an action-class σ. Ω₈ (mode-gate) is enforced
                                  downstream by MembraneBus.publish.
"""
from __future__ import annotations

from mebus import MMessage, is_action_layer

# Reconciled Ω-registry: id -> (statement, plane, owner/status)
OMEGA: dict[str, tuple[str, str, str]] = {
    "Ω1": ("P(collision | active) < ε", "safety", "Orbi / Pixhawk (out of scope here)"),
    "Ω2": ("human override reachable < 500 ms", "safety", "Orbi (out of scope here)"),
    "Ω3": ("safety-layer weights immutable to SMC", "integrity", "SMC (out of scope here)"),
    "Ω4": ("calibration drift < ε or HALT", "integrity", "CAL — TODO (Calibration Monitor)"),
    "Ω5": ("full autonomous operation offline", "sovereignty", "deployment"),
    "Ω6": ("natural language ∉ core (structured payloads)", "non-anthropomorphic", "ENFORCED here"),
    "Ω7": ("every emission carries provenance / causal log", "provenance", "ENFORCED here"),
    "Ω8": ("μ mode-gate: action suppressed in DREAM", "mode", "ENFORCED by MembraneBus.publish"),
}


class InvViolation(Exception):
    """Raised when an emission would violate an enforced invariant."""


def gate_emit(msg: MMessage) -> MMessage:
    """Validate an outbound Urbi message against the locally-enforced invariants."""
    # Urbi-non-actuation: the auditor produces belief, never action (3-6-9 governs the loop,
    # it does not enter it). This is the structural reason Urbi can audit Orbi.
    if is_action_layer(msg.sigma):
        raise InvViolation(f"Urbi may not emit action-class σ={msg.sigma!r} (audits, never acts)")

    # Ω₆ — the canonical representation must be structured, not a bare NL blob.
    if not isinstance(msg.payload, dict):
        raise InvViolation("Ω6: payload (π) must be structured, not natural language")
    if msg.sigma == "m.belief" and ("state" not in msg.payload or "confidence" not in msg.payload):
        raise InvViolation("Ω6: m.belief must carry structured {state, confidence}")

    # Ω₇ — provenance present (context for beliefs, causal_parents for records).
    has_prov = bool((msg.context or {}).get("provenance")) or bool(msg.payload.get("causal_parents"))
    if not has_prov:
        raise InvViolation("Ω7: emission must carry provenance / causal parents")

    return msg

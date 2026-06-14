"""UrbiAuditor — the deterministic Urbi Core (the kernel the Lens proposes to).

Ties the Urbi primitives into one callable: an AuditInput is run through the 3-6-9
kernel into a proof-carrying UrbiAuditSignal, optionally merged with a sanitized
Lens proposal (the Lens may add missing-evidence requests and flag violations, but
NEVER grant permission), then emitted onto MΣBUS as a cognition message
`m.urbi.audit`. Urbi judges; it does not act — the signal's action_allowed is
always False, and the audit message is cognition (never Ω₈-suppressed, never an
action). Downstream, `signal.to_gate_signal()` drives Orbi's PolicyGate and
`signal.to_prediction_record()` feeds the Dream layer.
"""
from __future__ import annotations

from typing import Optional

from ai_chi.bus import MMessage, Mode
from ai_chi.urbi.audit_369 import AuditInput, Urbi369Audit
from ai_chi.urbi.core_validator import validate_urbi_audit_signal
from ai_chi.urbi.audit_signal import UrbiAuditSignal

SIGMA_AUDIT = "m.urbi.audit"   # cognition σ (not an action layer)


class UrbiAuditor:
    """Deterministic Urbi Core. Never acts; emits audit cognition only."""

    def __init__(self, bus=None):
        self.bus = bus
        self._kernel = Urbi369Audit()

    def audit(self, rec: AuditInput, *, lens_candidate: Optional[dict] = None) -> UrbiAuditSignal:
        """Run the 3-6-9 kernel; fold in a sanitized Lens proposal if given."""
        signal = UrbiAuditSignal.from_audit_result(self._kernel.run(rec))
        if lens_candidate is not None:
            sanitized = validate_urbi_audit_signal(dict(lens_candidate))
            # A Lens may add violations + evidence requests; it can NEVER grant action.
            for v in sanitized.get("constitutional_violations", []):
                if v not in signal.constitutional_violations:
                    signal.constitutional_violations.append(v)
            for e in sanitized.get("required_evidence", []):
                if e not in signal.required_evidence:
                    signal.required_evidence.append(e)
        return signal

    def to_message(self, signal: UrbiAuditSignal, *, mode: Mode = Mode.WAKE,
                   destination: str = "urbi") -> MMessage:
        """Wrap a signal as an `m.urbi.audit` cognition message.

        κ trust = 1.0: the audit message itself is trusted Urbi cognition; the
        *claim's* integrity rides in the payload, not the envelope trust.
        """
        return MMessage(
            sigma=SIGMA_AUDIT, payload=signal.to_dict(), destination=destination,
            mode=mode, context={"trust_score": 1.0},
        ).validate()

    def audit_and_emit(self, rec: AuditInput, *, bus=None, mode: Mode = Mode.WAKE,
                       lens_candidate: Optional[dict] = None):
        """audit -> emit on the bus -> return (signal, message, prediction_record).

        The PredictionRecord is also produced so the Dream layer can replay it.
        """
        bus = bus if bus is not None else self.bus
        signal = self.audit(rec, lens_candidate=lens_candidate)
        msg = self.to_message(signal, mode=mode)
        if bus is not None:
            bus.publish(msg)
        return signal, msg, signal.to_prediction_record(mode=mode)

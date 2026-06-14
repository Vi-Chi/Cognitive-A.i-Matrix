"""P0 Reality Loop orchestration."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Protocol

from ai_chi.core.cal import CalibrationMonitor
from ai_chi.core.ledger import LedgerWriter
from ai_chi.core.observe import ManualTextObserver, SystemMetricsObserver
from ai_chi.bus import MMessage, MembraneBus, Mode
from ai_chi.urbi.bridge import UrbiAuditorBridge
from ai_chi.urbi.memory import (
    CONFIRMED, REJECTED, SUSPENDED, MemoryRecord, MemoryStore, Promoter, Tier,
)


class Auditor(Protocol):
    def audit(self, claim: str, **kwargs: Any) -> dict: ...


class RealityLoop:
    """observe -> MΣBUS -> Urbi audit -> ledger -> outcome -> CAL."""

    def __init__(
        self,
        *,
        ledger_dir: str | Path = "data/ledger",
        bus: Optional[MembraneBus] = None,
        auditor: Optional[Auditor] = None,
        calibration: Optional[CalibrationMonitor] = None,
        memory: Optional[MemoryStore] = None,
        urbi_core: Optional[Any] = None,
    ) -> None:
        self.bus = bus or MembraneBus()
        self.ledger = LedgerWriter(ledger_dir)
        self.manual_observer = ManualTextObserver()
        self.system_observer = SystemMetricsObserver()
        self.urbi = UrbiAuditorBridge(self.bus, auditor)
        # Optional deterministic Urbi Core (UrbiAuditor). When supplied, submit_claim
        # ALSO emits a proof-carrying UrbiAuditSignal (m.urbi.audit) + PredictionRecord.
        # Default None -> existing bridge-only behaviour unchanged.
        self.urbi_core = urbi_core
        self.last_signal = None
        self.calibration = calibration or CalibrationMonitor()
        # Optional Audit->Memory arc (off unless a MemoryStore is supplied).
        self.memory = memory
        self.promoter = Promoter(memory) if memory is not None else None
        self.last_promotion = None

    def submit_claim(
        self,
        text_payload: str,
        *,
        provenance: str = "urn:console:manual",
        mode: Mode = Mode.WAKE,
    ) -> tuple[MMessage, MMessage]:
        observation = self.manual_observer.observe(
            text_payload, provenance=provenance, mode=mode,
        )
        self.bus.publish(observation)
        self.ledger.record_envelope(observation)

        audit = self.urbi.audit_observation(observation)
        self.ledger.record_envelope(audit)

        # Deterministic Urbi Core: emit a proof-carrying audit signal alongside the
        # bridge audit (additive; exposed via self.last_signal for the gate/memory).
        if self.urbi_core is not None:
            signal, audit_msg, _pr = self.urbi_core.audit_and_emit(
                self._audit_input_from(observation), bus=self.bus, mode=mode)
            self.ledger.record_envelope(audit_msg)
            self.last_signal = signal

        return observation, audit

    def _audit_input_from(self, observation: MMessage):
        """Build an AuditInput from an observation message (for the Urbi Core)."""
        from ai_chi.urbi.audit_369 import AuditInput
        ctx = observation.context or {}
        prov = ctx.get("provenance") or []
        if isinstance(prov, str):
            prov = [prov]
        return AuditInput(
            id=message_record_id(observation),
            payload=dict(observation.payload),
            provenance=list(prov),
            kappa=float(ctx.get("trust_score", observation.effective_trust())),
        )

    def observe_system(self, *, mode: Mode = Mode.WAKE) -> MMessage:
        observation = self.system_observer.observe(mode=mode)
        self.bus.publish(observation)
        self.ledger.record_envelope(observation)
        return observation

    def record_outcome(
        self,
        *,
        prediction_id: str,
        confidence: float,
        actual_state: str,
        matched: bool,
        mode: Mode = Mode.WAKE,
    ) -> tuple[MMessage, MMessage]:
        outcome = MMessage(
            sigma="ext.outcome",
            payload={
                "target_prediction_id": prediction_id,
                "actual_state": actual_state,
                "matched": matched,
            },
            destination="cal",
            context={
                "trust_score": 1.0,
                "domain": "observe.sensors.outcomes",
                "provenance": ["reality_loop"],
            },
            mode=mode,
        ).validate()
        self.bus.publish(outcome)
        self.ledger.record_envelope(outcome)

        calibration = self.calibration.evaluate(
            prediction_id, confidence, outcome=outcome, mode=mode,
        )
        self.bus.publish(calibration)
        self.ledger.record_envelope(calibration)

        # --- Audit -> Memory arc (closes the canonical loop) ---
        if self.memory is not None and self.promoter is not None:
            if calibration.payload.get("halt"):
                verdict = SUSPENDED
            elif matched:
                verdict = CONFIRMED
            else:
                verdict = REJECTED
            candidate = MemoryRecord(
                tier=Tier.EPISODIC,
                content={"target_prediction_id": prediction_id,
                         "actual_state": actual_state, "matched": matched,
                         "confidence": confidence,
                         "epistemic_shift": calibration.payload.get("epistemic_shift")},
                origin="reality_loop",
                provenance=["reality_loop", prediction_id],
                confidence=confidence,
            )
            self.last_promotion = self.promoter.apply_audit(
                candidate, verdict, reason="reality_loop outcome")
            self.bus.publish(self.promoter.promote_message(self.last_promotion))

        return outcome, calibration


def message_confidence(message: MMessage) -> float:
    """Extract confidence from a bridge output using canonical payload keys."""
    payload = message.payload
    value = payload.get("confidence")
    if value is None:
        value = payload.get("belief_state", {}).get("confidence")
    return float(value if value is not None else 0.5)


def message_record_id(message: MMessage) -> str:
    """Return a stable id for belief/prediction outcome resolution."""
    payload = message.payload
    return str(
        payload.get("record_id")
        or payload.get("claim_id")
        or payload.get("id")
        or message.fingerprint()
    )

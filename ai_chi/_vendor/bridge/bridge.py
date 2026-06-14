"""Urbi <-> MΣBUS bridge — wires the running v2.1 tri-state 3-6-9 auditor onto the membrane.

Canon (2026-06-07): Urbi is the Yin / 3-6-9 governing axis. It produces *audited belief* and
NEVER acts. This bridge takes TriStateAuditor verdicts and emits them as cognition-class MΣBUS
messages, so Urbi speaks on the same wire as Orbi (Yang / 2-4-6-8) and Autopoiesis.

Mapping (3-6-9 verdict -> M-protocol payload class):
    [+] confirmed  -> m.belief             (audited belief, surfaced)
    [-] rejected   -> m.belief             (audited belief, rejected)
    [=] suspended  -> m.prediction_record  (the dream-layer synapse -> ΦΔ)

Every emission is cognition (m.*), never action (m.action / cm.* act / cmd.*), so Ω₈ never
suppresses Urbi belief — and the INV gate refuses to let Urbi emit anything action-class.

The auditor module (audit.py) is imported lazily and unmodified; its Ollama endpoint is
repointed at Hailo-Ollama via `bridge.endpoint` (see that module).
"""
from __future__ import annotations

from typing import Any, Optional, Protocol

from mebus import (
    MMessage, MembraneBus, Mode, PredictionRecord, DomainTag,
    monotonic_tau, is_action_layer,
)

from .inv import gate_emit

DEFAULT_DOMAIN = DomainTag.SYSTEM_AUDIT.value
SOURCE = "urbi"
PROVENANCE_TAG = "tri_state_369_v2.1"


class Auditor(Protocol):
    """Anything that returns a v2.1 verdict dict {state, confidence, reason, route}."""
    def audit(self, claim: str, **kwargs: Any) -> dict: ...


class UrbiMebusBridge:
    """Bridge a TriStateAuditor onto a MembraneBus.

    auditor may be injected (tests / custom); if None, the live TriStateAuditor is
    constructed lazily on first use (so importing the bridge never touches Ollama).
    """

    def __init__(
        self,
        bus: MembraneBus,
        auditor: Optional[Auditor] = None,
        *,
        source: str = SOURCE,
        destination: str = "orbi",
        mode: Mode = Mode.WAKE,
    ) -> None:
        self.bus = bus
        self._auditor = auditor
        self.source = source
        self.destination = destination
        self.mode = mode

    @property
    def auditor(self) -> Auditor:
        if self._auditor is None:
            import sys
            import pathlib
            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
            from .endpoint import apply_to_auditor
            apply_to_auditor()
            from audit import TriStateAuditor  # type: ignore[import-not-found]
            self._auditor = TriStateAuditor()
        return self._auditor

    def set_mode(self, mode: Mode) -> None:
        """Set the current tri-state mode (μ). Mirrors ΦΨ arbitration WAKE/LIMINAL/DREAM."""
        self.mode = mode

    def verdict_to_message(self, claim: str, verdict: dict, *, mode: Optional[Mode] = None) -> MMessage:
        """Map a 3-6-9 verdict to a validated, INV-gated MΣBUS message."""
        mode = mode or self.mode
        state = verdict["state"]
        conf = float(verdict["confidence"])
        reason = str(verdict.get("reason", ""))
        route = str(verdict.get("route", ""))
        provenance = [self.source, PROVENANCE_TAG]

        if state == "=":
            # Genuine epistemic suspension -> the dream synapse. (The [=] state is precious:
            # model indecision != epistemic uncertainty.)
            rec = PredictionRecord(
                record_id=f"urbi-audit-{monotonic_tau()}",
                belief_state={"claim": claim, "lens_reason": reason},
                predicted_outcome={"resolvable_in_dream": True, "route": route or "dream_layer"},
                domain=DEFAULT_DOMAIN,
                confidence=conf,
                mu_at_time=mode,
                causal_parents=provenance,
            )
            msg = rec.to_message(destination=self.destination, mode=mode)
        else:
            payload = {
                "claim": claim,
                "state": state,            # "+" | "-" — structured, not NL (Ω₆)
                "confidence": conf,        # calibrated κ
                "route": route,
                "lens_trace": reason,      # human-readable trace only (metadata)
                "auditor": PROVENANCE_TAG,
            }
            context = {
                "trust_score": conf,
                "domain": DEFAULT_DOMAIN,
                "provenance": provenance,
            }
            msg = MMessage(
                sigma="m.belief", payload=payload,
                destination=self.destination, mode=mode, context=context,
            ).validate()

        gate_emit(msg)  # INV: Ω₆ structured, Ω₇ provenance, Urbi-non-actuation
        return msg

    def audit_and_publish(self, claim: str, *, mode: Optional[Mode] = None, strict: bool = False) -> dict:
        """Audit a claim and publish the verdict on the bus. Returns verdict/message/delivered."""
        verdict = self.auditor.audit(claim)
        msg = self.verdict_to_message(claim, verdict, mode=mode)
        delivered = self.bus.publish(msg, strict=strict)
        return {"verdict": verdict, "message": msg, "delivered": delivered}

    def subscribe_requests(self, sigma: str = "m.audit_request") -> None:
        """Listen for inbound audit requests on the bus and answer with a published verdict."""
        def _handler(req: MMessage) -> None:
            claim = (req.payload or {}).get("claim")
            if not claim:
                return
            self.audit_and_publish(claim, mode=req.mode)
        self.bus.subscribe(sigma, _handler)

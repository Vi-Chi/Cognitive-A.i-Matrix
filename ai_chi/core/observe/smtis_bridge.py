"""SMTIS → core bridge — a translation membrane for maritime advisory cognition.

SMTIS (the read-only maritime app) emits its own `PredictionRecord` shape (TypeScript:
id, mode LIVE/SIMULATION/REPLAY, kind, summary, confidence, risk_score, source_inputs,
alternatives, audit{...safe_for_action}). This bridge maps it onto the canonical
`mebus.PredictionRecord` so Urbi can audit it and the DREAM Replay Auditor can replay it.

Reason to exist (the membrane's hard rule): **a record that claims it is safe for action
is refused, fail-closed.** SMTIS's own invariant is `safe_for_action` must always be False;
this bridge enforces it at the boundary — no action-permitting cognition crosses into the
core. (Whether an action is *allowed* remains Urbi's call, and Urbi's answer is always False;
the bridge simply refuses to admit a foreign claim to the contrary.)

Mode mapping mirrors the documented seam:
  LIVE → WAKE · SIMULATION → LIMINAL (advisory/degraded) · REPLAY → DREAM (replay vs outcome).

Stdlib only.
"""
from __future__ import annotations

import logging
from typing import Optional

from ai_chi.bus import MMessage, MembraneBus, Mode, PredictionRecord

_LOG = logging.getLogger(__name__)

SMTIS_MODE_MAP: dict[str, Mode] = {
    "LIVE": Mode.WAKE,
    "SIMULATION": Mode.LIMINAL,
    "REPLAY": Mode.DREAM,
}


class SmtisBridgeError(ValueError):
    """Raised when a SMTIS record cannot cross the membrane (e.g. claims action-safety)."""


def _safe_for_action_is_false(audit: dict) -> bool:
    """Fail-closed: only an explicit `safe_for_action == False` is acceptable."""
    return isinstance(audit, dict) and audit.get("safe_for_action", True) is False


def prediction_record_from_smtis(d: dict) -> PredictionRecord:
    """Map one SMTIS PredictionRecord payload → canonical mebus.PredictionRecord.

    Refuses (SmtisBridgeError) any record whose audit does not explicitly set
    safe_for_action=False, or whose mode is unknown.
    """
    if not isinstance(d, dict):
        raise SmtisBridgeError("SMTIS record must be a dict")

    audit = d.get("audit", {})
    if not _safe_for_action_is_false(audit):
        raise SmtisBridgeError(
            f"refused: record {d.get('id')!r} does not assert safe_for_action=False "
            f"(fail-closed; the membrane admits no action-permitting cognition)"
        )

    raw_mode = str(d.get("mode", "")).upper()
    mu = SMTIS_MODE_MAP.get(raw_mode)
    if mu is None:
        raise SmtisBridgeError(f"unknown SMTIS mode {d.get('mode')!r} (expected LIVE/SIMULATION/REPLAY)")

    kind = d.get("kind", "forecast")
    predicted_outcome = {
        "summary": d.get("summary", ""),
        "kind": kind,
        "prediction_for": d.get("prediction_for"),
        "risk_score": d.get("risk_score"),
        "alternatives": list(d.get("alternatives", [])),
        # provenance of the refusal-checked safety flags, preserved for audit:
        "smtis_audit": dict(audit),
        # the core never trusts a foreign action claim; record the membrane's stance:
        "action_admissible": False,
    }
    belief_state = {"prediction_for": d.get("prediction_for"), "kind": kind}

    return PredictionRecord(
        record_id=str(d.get("id") or ""),
        belief_state=belief_state,
        predicted_outcome=predicted_outcome,
        domain=f"smtis.{kind}",
        mu_at_time=mu,
        actual_outcome=d.get("actual_outcome"),          # present only when REPLAY has an outcome
        prediction_error=d.get("prediction_error"),
        confidence=float(d.get("confidence", 0.5)),
        causal_parents=list(d.get("source_inputs", [])),  # which raw feeds fed the forecast
    )


class SmtisPredictionBridge:
    """Ingest SMTIS advisory predictions onto the membrane as `m.prediction_record` cognition.

    Never acts; refuses action-permitting records; emits cognition only (Urbi audits it,
    and in REPLAY/DREAM the Dream Replay Auditor consumes it).
    """

    def __init__(self, bus: Optional[MembraneBus] = None, *, destination: str = "urbi") -> None:
        self.bus = bus
        self.destination = destination

    def to_record(self, smtis_payload: dict) -> PredictionRecord:
        return prediction_record_from_smtis(smtis_payload)

    def ingest(self, smtis_payload: dict, *, bus: Optional[MembraneBus] = None) -> MMessage:
        """Translate, publish as m.prediction_record cognition, return the message."""
        rec = self.to_record(smtis_payload)
        msg = rec.to_message(destination=self.destination, mode=rec.mu_at_time)
        if msg.is_action:  # m.prediction_record is cognition; never an action layer
            raise AssertionError("SMTIS bridge produced an action-layer message")
        target = bus if bus is not None else self.bus
        if target is not None:
            target.publish(msg)
        return msg

    def ingest_many(self, payloads) -> list[PredictionRecord]:
        """Translate a batch (e.g. a REPLAY session) into records for a DREAM cycle.

        Malformed/refused records are skipped (logged), not fatal — a bad forecast must
        not abort the consolidation of the good ones.
        """
        out: list[PredictionRecord] = []
        for p in payloads:
            try:
                out.append(self.to_record(p))
            except SmtisBridgeError as e:
                _LOG.warning("SMTIS bridge refused a record: %s", e)
        return out

"""DREAM replay engine — ordered, offline, no-world-action replay of PredictionRecords.

Stdlib only (no DuckDB): the timeline is a deterministic in-memory sort. Replay never
executes, commands, or writes world state — it only re-presents past cognition for
consolidation. Priority targets are the high-confidence-wrong records (the Dream
Layer's primary learning signal, per PredictionRecord.is_high_confidence_wrong).
"""
from __future__ import annotations

from ai_chi.bus import PredictionRecord


class DreamReplayEngine:
    def __init__(self) -> None:
        self._records: list[PredictionRecord] = []

    def load(self, records) -> "DreamReplayEngine":
        self._records = list(records)
        return self

    def replay_timeline(self) -> list[PredictionRecord]:
        """Causal order: by tau_start (None last), then record_id — stable + deterministic."""
        def key(r: PredictionRecord):
            t = r.tau_start if r.tau_start is not None else float("inf")
            return (t, str(r.record_id))
        return sorted(self._records, key=key)

    def priority_targets(self) -> list[PredictionRecord]:
        """High-confidence-wrong records: replay these first; they teach the most."""
        return [r for r in self._records if r.is_high_confidence_wrong()]


def prediction_record_from_payload(d: dict) -> PredictionRecord:
    """Reconstruct a PredictionRecord from its `to_payload()` dict (bus π / JSONL line)."""
    from ai_chi.bus import Mode
    mu = d.get("mu_at_time", "WAKE")
    return PredictionRecord(
        record_id=str(d.get("record_id") or d.get("claim_id") or ""),
        belief_state=d.get("belief_state", {}),
        predicted_outcome=d.get("predicted_outcome", {}),
        domain=d.get("domain", "unknown"),
        mu_at_time=Mode(mu) if mu in Mode._value2member_map_ else Mode.WAKE,
        actual_outcome=d.get("actual_outcome"),
        prediction_error=d.get("prediction_error"),
        confidence=float(d.get("confidence", 0.5)),
        causal_parents=list(d.get("causal_parents", [])),
        error_type=d.get("error_type"),
        tau_start=d.get("tau_start"),
        tau_end=d.get("tau_end"),
        reversal_candidate=bool(d.get("reversal_candidate", False)),
        void_related=bool(d.get("void_related", False)),
    )

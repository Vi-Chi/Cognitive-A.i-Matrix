"""PredictionRecord — the cognition synapse.

Emitted by Orbi/Urbi agents in WAKE; consumed by the Urbi Dream Layer (ΦΔ) in DREAM.
The unblocking primitive: action → outcome → error → reliability → dream learning.
Carried on MΣBUS as the π of an `m.prediction_record` message.

Superset of the two source definitions: the canonical MEBUS v0.1 record and the richer
prototype record in `M-Protocol + Sigma Bus_prototype.txt` (error_type, tau window,
reversal/void flags, helper predicates). New fields are optional → back-compatible.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

from .protocol import MMessage, Mode


@dataclass
class PredictionRecord:
    record_id: str
    belief_state: dict
    predicted_outcome: dict
    domain: str
    mu_at_time: Mode = Mode.WAKE
    actual_outcome: Optional[dict] = None
    prediction_error: Optional[float] = None     # KL divergence predicted vs actual
    confidence: float = 0.5
    causal_parents: list = field(default_factory=list)
    # --- recovered from the prototype record (optional, back-compatible) ---
    error_type: Optional[str] = None             # "high_conf_wrong", "uncertain_right", ...
    tau_start: Optional[int] = None
    tau_end: Optional[int] = None
    reversal_candidate: bool = False
    void_related: bool = False

    def is_high_confidence_wrong(self) -> bool:
        """High confidence + large error = the Dream Layer's priority replay target."""
        return (self.confidence > 0.8
                and self.prediction_error is not None
                and self.prediction_error > 0.3)

    def classify_error(self) -> Optional[str]:
        """Set and return error_type from confidence vs error (when an error is known)."""
        if self.prediction_error is None:
            return None
        if self.is_high_confidence_wrong():
            self.error_type = "high_conf_wrong"
        elif self.confidence < 0.4 and self.prediction_error <= 0.3:
            self.error_type = "uncertain_right"
        else:
            self.error_type = "nominal"
        return self.error_type

    def to_payload(self) -> dict:
        d = asdict(self)
        d["mu_at_time"] = self.mu_at_time.value
        return d

    def to_message(self, *, destination: str = "urbi", mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(sigma="m.prediction_record", payload=self.to_payload(),
                        destination=destination, mode=mode).validate()

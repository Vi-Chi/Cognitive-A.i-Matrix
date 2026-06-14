"""Shared gate verdict type."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Verdict(Enum):
    ALLOW = "allow"
    DENY = "deny"
    HOLD = "hold"
    SANDBOX = "sandbox"
    MANUAL_REVIEW = "manual_review"


@dataclass
class Decision:
    verdict: Verdict
    reasons: list = field(default_factory=list)
    gate: str = ""

    @property
    def allowed(self) -> bool:
        return self.verdict is Verdict.ALLOW

    def to_dict(self) -> dict:
        return {"verdict": self.verdict.value, "gate": self.gate, "reasons": list(self.reasons)}

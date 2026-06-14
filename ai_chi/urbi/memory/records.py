"""Urbi memory records + the six-tier model (cognition only, never action).

From `urbi-vm.txt`: Urbi's memory is tiered by trust, and the sacred property is a
**membrane between sandbox experience and core belief** — nothing becomes trusted
without audit, so the system cannot poison itself with its own dreams.

Tiers (trust gradient):
  RAW         untrusted intake, verbatim
  QUARANTINE  untrusted but preserved (scraped/LLM/agent output, outliers)
  EPISODIC    what happened (events, runs, traces)
  SEMANTIC    what Urbi *thinks* it learned (candidate claims)
  PROCEDURAL  reusable skills (guarded — a bad skill repeats failures)
  NEGATIVE    known-bad paths / dead ends (preserved, high value)
  CORE        promoted / trusted (only the Promoter may write here)

truth_state mirrors the 3-6-9 auditor: [+] confirmed, [-] rejected, [=] suspended.
The `[=]` state is precious — sandbox dreams should produce *many* `[=]`, not forced
certainty. Every record carries provenance: **no memory without provenance.**

σ-classes are cognition (`m.*`) → never action → Ω₈-safe; they flow in DREAM.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from ai_chi.bus import MMessage, Mode, monotonic_tau

SIGMA_MEMORY = "m.memory"
SIGMA_PROMOTION = "m.memory_promotion"

# truth states (same alphabet as Urbi audit + AIDICT audit_signal)
CONFIRMED = "+"
REJECTED = "-"
SUSPENDED = "="

DOMAIN = "urbi.memory"


class Tier(str, Enum):
    RAW = "raw"
    QUARANTINE = "quarantine"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    NEGATIVE = "negative"
    CORE = "core"


# Candidate tiers an item may sit in before promotion. CORE is reachable ONLY via
# the Promoter (core-write monopoly).
CANDIDATE_TIERS = frozenset({
    Tier.RAW, Tier.QUARANTINE, Tier.EPISODIC, Tier.SEMANTIC, Tier.PROCEDURAL,
})


def _short_hash(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12]


@dataclass
class MemoryRecord:
    """A single memory item with trust tier, truth state, and mandatory provenance."""

    tier: Tier
    content: dict
    origin: str                       # sandbox|observe|dream|human|agent|external
    provenance: list[str]             # REQUIRED — no memory without provenance
    truth_state: str = SUSPENDED      # [+]/[-]/[=]; default suspended (precious)
    confidence: float = 0.4
    requires_external_validation: bool = True
    promotion_status: str = "candidate"   # candidate|promoted|rejected|quarantined
    source_episode: str = ""
    tau: int = field(default_factory=monotonic_tau)
    memory_id: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.tier, str):
            self.tier = Tier(self.tier)
        if not self.provenance:
            raise ValueError("MemoryRecord requires provenance (no memory without provenance)")
        if self.truth_state not in (CONFIRMED, REJECTED, SUSPENDED):
            raise ValueError(f"invalid truth_state {self.truth_state!r}")
        if not self.memory_id:
            self.memory_id = "mem_" + _short_hash(self.origin, self.tier.value,
                                                  self.content, self.tau)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["tier"] = self.tier.value
        d["record_type"] = "MemoryRecord"
        return d

    def to_message(self, *, sigma: str = SIGMA_MEMORY, destination: str = "urbi",
                   mode: Mode = Mode.WAKE) -> MMessage:
        # trust_score reflects extraction/holding confidence, not truth.
        return MMessage(
            sigma=sigma,
            payload=self.to_payload(),
            destination=destination,
            context={"trust_score": max(0.0, min(1.0, float(self.confidence))),
                     "domain": DOMAIN, "provenance": list(self.provenance)},
            mode=mode,
        ).validate()

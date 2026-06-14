"""Promoter — the audit-gated membrane between candidate memory and trusted CORE.

This is the ONLY path that writes the CORE tier, and it does so **only on an
external audit verdict** — never on the record's own self-claimed truth_state. That
is the out-of-loop property applied to memory: a candidate cannot authorise its own
promotion, so the system cannot poison itself with its own dreams.

    audit verdict [+]  -> copy to CORE (promoted, validation no longer required)
    audit verdict [-]  -> move to NEGATIVE (rejected, *preserved* — known-bad is valuable)
    audit verdict [=]  -> stays QUARANTINE (candidate, still needs external validation)

The verdict is supplied by Urbi / CAL-Ω₄ from outside the memory subsystem (e.g., the
Reality Loop's calibrated outcome). The Promoter never derives it from the candidate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ai_chi.urbi.memory.records import (
    CONFIRMED, REJECTED, SUSPENDED, MemoryRecord, Tier,
)
from ai_chi.urbi.memory.store import _CORE_TOKEN, MemoryStore


@dataclass(frozen=True)
class PromotionOutcome:
    decision: str                 # promoted|rejected|quarantined
    result: MemoryRecord
    reason: str


class Promoter:
    """Moves candidates across the trust membrane under an external audit verdict."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def apply_audit(self, candidate: MemoryRecord, audit_verdict: str,
                    *, reason: str = "") -> PromotionOutcome:
        """Apply an EXTERNAL audit verdict to a candidate. Verdict is authoritative."""
        prov = list(candidate.provenance) + ["urbi.promoter"]

        if audit_verdict == CONFIRMED:
            promoted = MemoryRecord(
                tier=Tier.CORE, content=candidate.content, origin=candidate.origin,
                provenance=prov, truth_state=CONFIRMED, confidence=max(candidate.confidence, 0.8),
                requires_external_validation=False, promotion_status="promoted",
                source_episode=candidate.memory_id,
            )
            self.store.append(promoted, _core_token=_CORE_TOKEN)  # only path to CORE
            return PromotionOutcome("promoted", promoted, reason or "audit [+] -> CORE")

        if audit_verdict == REJECTED:
            rejected = MemoryRecord(
                tier=Tier.NEGATIVE, content=candidate.content, origin=candidate.origin,
                provenance=prov, truth_state=REJECTED, confidence=candidate.confidence,
                requires_external_validation=False, promotion_status="rejected",
                source_episode=candidate.memory_id,
            )
            self.store.append(rejected)  # preserved, not deleted
            return PromotionOutcome("rejected", rejected, reason or "audit [-] -> NEGATIVE (preserved)")

        # SUSPENDED or anything unrecognised -> fail-safe: keep as quarantined candidate.
        held = MemoryRecord(
            tier=Tier.QUARANTINE, content=candidate.content, origin=candidate.origin,
            provenance=prov, truth_state=SUSPENDED, confidence=candidate.confidence,
            requires_external_validation=True, promotion_status="quarantined",
            source_episode=candidate.memory_id,
        )
        self.store.append(held)
        return PromotionOutcome("quarantined", held, reason or "audit [=] / none -> stays QUARANTINE")

    def promote_message(self, outcome: PromotionOutcome):
        """Canonical bus event for the promotion (audit trail)."""
        from ai_chi.urbi.memory.records import SIGMA_PROMOTION
        return outcome.result.to_message(sigma=SIGMA_PROMOTION, destination="urbi.audit")

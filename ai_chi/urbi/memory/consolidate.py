"""Closed-dream consolidation — internal replay, no network, no promotion.

From `urbi-vm.txt`: closed dreams use no internet and no new data; they replay
internal memory to consolidate raw/quarantine/episodic material into SEMANTIC
*candidates*. Crucially, consolidation **never promotes** — every output is a `[=]`
candidate that still requires external validation. Outliers are preserved, not
compressed away (the "tree-of-life" rule).

Open dreams (network-allowed research) are intentionally NOT built here: they would
write to QUARANTINE only and need their own gate. Deferred.
"""
from __future__ import annotations

from ai_chi.urbi.memory.records import SUSPENDED, MemoryRecord, Tier
from ai_chi.urbi.memory.store import MemoryStore

# Tiers a closed dream is allowed to read (no CORE, no NEGATIVE rewrite).
_REPLAY_TIERS = (Tier.RAW, Tier.QUARANTINE, Tier.EPISODIC)


class MemoryConsolidator:
    """Offline (μ=DREAM) consolidation of candidate memory into semantic candidates."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def closed_dream(self) -> list[MemoryRecord]:
        """Replay candidate tiers -> SEMANTIC [=] candidates. Returns what was written."""
        produced: list[MemoryRecord] = []
        for tier in _REPLAY_TIERS:
            for raw in self.store.read(tier):
                prov = list(raw.get("provenance", [])) + ["urbi.dream.closed"]
                if not prov:
                    continue  # no memory without provenance
                candidate = MemoryRecord(
                    tier=Tier.SEMANTIC,
                    content={"consolidated_from": raw.get("memory_id", ""),
                             "summary": _summarise(raw)},
                    origin="dream",
                    provenance=prov,
                    truth_state=SUSPENDED,          # never promotes; precious [=]
                    confidence=min(float(raw.get("confidence", 0.4)), 0.5),
                    requires_external_validation=True,
                    source_episode=raw.get("memory_id", ""),
                )
                self.store.append(candidate)        # SEMANTIC, never CORE
                produced.append(candidate)
        return produced


def _summarise(raw: dict) -> str:
    content = raw.get("content", {})
    if isinstance(content, dict):
        keys = ", ".join(sorted(content)[:5])
        return f"{raw.get('origin','?')}::{keys}" if keys else str(raw.get("origin", "?"))
    return str(content)[:80]

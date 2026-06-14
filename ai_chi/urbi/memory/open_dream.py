"""Open dream — gated, network-allowed research that writes ONLY to quarantine.

From `urbi-vm.txt`: open dreams allow the network but are *dangerous* and "should
always write first to quarantine." Because a network fetch touches the world it is an
**action**, not pure cognition — so it must clear a gate (the growth rule: no
capability without its gate). Ω₈ forbids action in DREAM, so an open dream is an
Orbi-gated WAKE/LIMINAL research action, distinct from the closed (DREAM) consolidation.

This module stays decoupled from Orbi: the caller injects a ``gate_check`` (Orbi's
PolicyGate) and a ``fetch_fn`` (the actual fetcher). Fail-safe: **no gate → no
network.** Harvested material lands in QUARANTINE as `[=]`, untrusted, never promoted.
No fetcher ships here (same "no mass downloader" discipline as AIDICT).
"""
from __future__ import annotations

from typing import Callable, Optional

from ai_chi.urbi.memory.records import SUSPENDED, MemoryRecord, Tier
from ai_chi.urbi.memory.store import MemoryStore

# gate_check(query) -> True if Orbi's PolicyGate allows the research action.
GateCheck = Callable[[str], bool]
# fetch_fn(query) -> [{"content": dict|str, "source": str}] (caller-supplied, offline-safe).
FetchFn = Callable[[str], list[dict]]


class OpenDreamer:
    def __init__(self, store: MemoryStore, *, gate_check: Optional[GateCheck] = None,
                 fetch_fn: Optional[FetchFn] = None) -> None:
        self.store = store
        self.gate_check = gate_check
        self.fetch_fn = fetch_fn

    def run(self, query: str) -> list[MemoryRecord]:
        """Gated research. Returns quarantine records written, or [] if denied/no-op."""
        # Fail-safe: without an explicit gate grant, no network happens.
        if self.gate_check is None or not self.gate_check(query):
            return []
        if self.fetch_fn is None:
            return []
        produced: list[MemoryRecord] = []
        for item in self.fetch_fn(query) or []:
            source = str(item.get("source", "unknown"))
            content = item.get("content", item)
            rec = MemoryRecord(
                tier=Tier.QUARANTINE,           # open-dream output is ALWAYS untrusted
                content=content if isinstance(content, dict) else {"text": str(content)},
                origin="dream.open",
                provenance=["dream.open", source, f"query:{query}"],
                truth_state=SUSPENDED,
                confidence=0.2,                 # low — network noise, needs validation
                requires_external_validation=True,
            )
            self.store.append(rec)              # QUARANTINE, never CORE
            produced.append(rec)
        return produced

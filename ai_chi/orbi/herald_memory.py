"""Herald ↔ Urbi memory binding — a tier-scoped, READ-ONLY view per herald.

The DPHA 12-fold canon maps each herald to a memory manifold (T0–T5). This binds
that to the live Urbi memory store: a herald may read **only** the trust tiers its
manifold corresponds to, and may **never write** (CORE is the Promoter's monopoly;
heralds are bounded ghosts). "No capability without its gate" applied to memory.

Herald (manifold)            → readable Urbi trust tiers
  Lumen   Sight   T0 working   → RAW, EPISODIC          (the present field, recent traces)
  Mneme   Memory  T1 episodic  → EPISODIC, SEMANTIC, CORE (proven lineage)
  Logos   Meaning T2 semantic  → SEMANTIC                (concepts/claims)
  Artifex Making  T3 procedural→ PROCEDURAL              (reusable skills)
  Noctis  Night   T4 divergence→ NEGATIVE, QUARANTINE    (dead-ends, untrusted/outliers)
  Nomos   Law     T5 salience  → CORE, NEGATIVE          (weigh trusted vs forbidden)
"""
from __future__ import annotations

from ai_chi.urbi.memory import MemoryStore, Tier
from ai_chi.orbi.herald import HeraldArchetype, HeraldContract, by_name

# Each herald reads only its mapped trust tiers (read-only; no herald writes memory).
HERALD_READABLE_TIERS: dict[HeraldArchetype, frozenset] = {
    HeraldArchetype.SIGHT:   frozenset({Tier.RAW, Tier.EPISODIC}),
    HeraldArchetype.MEMORY:  frozenset({Tier.EPISODIC, Tier.SEMANTIC, Tier.CORE}),
    HeraldArchetype.MEANING: frozenset({Tier.SEMANTIC}),
    HeraldArchetype.FORGE:   frozenset({Tier.PROCEDURAL}),
    HeraldArchetype.SHADOW:  frozenset({Tier.NEGATIVE, Tier.QUARANTINE}),
    HeraldArchetype.LAW:     frozenset({Tier.CORE, Tier.NEGATIVE}),
}


class HeraldMemoryError(PermissionError):
    """Raised when a herald reads a tier outside its remit."""


class HeraldMemoryAccess:
    """A tier-scoped, read-only Urbi-memory view bound to one herald contract."""

    def __init__(self, store: MemoryStore, herald: HeraldContract):
        self.store = store
        self.herald = herald
        self.readable = HERALD_READABLE_TIERS.get(herald.archetype, frozenset())

    @classmethod
    def for_herald(cls, store: MemoryStore, name: str) -> "HeraldMemoryAccess":
        herald = by_name(name)
        if herald is None:
            raise HeraldMemoryError(f"unknown herald {name!r}")
        return cls(store, herald)

    def readable_tiers(self) -> frozenset:
        return frozenset(self.readable)

    def can_read(self, tier) -> bool:
        return Tier(tier) in self.readable

    def read(self, tier) -> list[dict]:
        t = Tier(tier)
        if t not in self.readable:
            allowed = sorted(x.value for x in self.readable)
            raise HeraldMemoryError(
                f"{self.herald.name} (Herald tier {self.herald.memory_tier}) may not read "
                f"'{t.value}'; readable = {allowed}")
        return self.store.read(t)


def herald_tier_map() -> dict[str, list[str]]:
    """Canonical {herald name: [readable tier values]} for docs/inspection."""
    out = {}
    for arch, tiers in HERALD_READABLE_TIERS.items():
        from ai_chi.orbi.herald import HERALD_NAMES
        out[HERALD_NAMES[arch]] = sorted(t.value for t in tiers)
    return out

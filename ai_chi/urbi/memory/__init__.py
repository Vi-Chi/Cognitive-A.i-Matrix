"""Urbi memory — tiered, audit-gated cognition store (never acts).

The cognition counterpart to Orbi's execution core. Six trust tiers + a hard
promotion membrane so sandbox/dream experience cannot become trusted belief without
external audit. Filesystem-first; LMDB/RocksDB can back it later behind this API.

Loop (from urbi-vm.txt):  Memory → Dream → (Sandbox) → PredictionRecord → Audit → Memory
This module owns Memory + closed-Dream + the Promotion membrane; the Sandbox/exec
side is Orbi's (gated), and Audit is Urbi/CAL (out-of-loop).
"""
from __future__ import annotations

from ai_chi.urbi.memory.records import (
    CONFIRMED, REJECTED, SUSPENDED, SIGMA_MEMORY, SIGMA_PROMOTION, MemoryRecord, Tier,
)
from ai_chi.urbi.memory.store import CoreWriteForbidden, MemoryStore
from ai_chi.urbi.memory.promotion import Promoter, PromotionOutcome
from ai_chi.urbi.memory.consolidate import MemoryConsolidator
from ai_chi.urbi.memory.open_dream import OpenDreamer
from ai_chi.urbi.memory.consult import negative_matches, procedural_skills

__all__ = [
    "MemoryRecord", "Tier", "MemoryStore", "CoreWriteForbidden",
    "Promoter", "PromotionOutcome", "MemoryConsolidator", "OpenDreamer",
    "negative_matches", "procedural_skills",
    "CONFIRMED", "REJECTED", "SUSPENDED", "SIGMA_MEMORY", "SIGMA_PROMOTION",
]

"""Herald ↔ Urbi memory binding: tier-scoped, read-only access per herald."""
import tempfile
import unittest
from pathlib import Path

from ai_chi.urbi.memory import MemoryStore, MemoryRecord, Tier
from ai_chi.orbi.herald_memory import (
    HeraldMemoryAccess, HeraldMemoryError, HERALD_READABLE_TIERS, herald_tier_map,
)
from ai_chi.orbi.herald import HeraldArchetype


def _store(tmp):
    s = MemoryStore(base_dir=Path(tmp) / "mem")
    # seed a few non-CORE tiers (CORE needs the Promoter token)
    for tier in (Tier.RAW, Tier.EPISODIC, Tier.SEMANTIC, Tier.PROCEDURAL, Tier.NEGATIVE, Tier.QUARANTINE):
        s.append(MemoryRecord(tier=tier, content={"t": tier.value}, origin="observe",
                              provenance=["seed"]))
    return s


class HeraldMemoryTests(unittest.TestCase):
    def test_lumen_reads_episodic_not_semantic(self):
        with tempfile.TemporaryDirectory() as tmp:
            acc = HeraldMemoryAccess.for_herald(_store(tmp), "Lumen")
            self.assertTrue(acc.can_read(Tier.EPISODIC))
            self.assertEqual(len(acc.read(Tier.EPISODIC)), 1)
            self.assertFalse(acc.can_read(Tier.SEMANTIC))
            with self.assertRaises(HeraldMemoryError):
                acc.read(Tier.SEMANTIC)

    def test_logos_reads_only_semantic(self):
        with tempfile.TemporaryDirectory() as tmp:
            acc = HeraldMemoryAccess.for_herald(_store(tmp), "Logos")
            self.assertEqual(acc.readable_tiers(), frozenset({Tier.SEMANTIC}))
            self.assertEqual(len(acc.read(Tier.SEMANTIC)), 1)
            with self.assertRaises(HeraldMemoryError):
                acc.read(Tier.PROCEDURAL)

    def test_noctis_reads_failure_paths_not_core(self):
        with tempfile.TemporaryDirectory() as tmp:
            acc = HeraldMemoryAccess.for_herald(_store(tmp), "Noctis")
            self.assertTrue(acc.can_read(Tier.NEGATIVE))
            self.assertTrue(acc.can_read(Tier.QUARANTINE))
            self.assertFalse(acc.can_read(Tier.CORE))   # shadow never touches trusted CORE

    def test_artifex_reads_procedural(self):
        with tempfile.TemporaryDirectory() as tmp:
            acc = HeraldMemoryAccess.for_herald(_store(tmp), "Artifex")
            self.assertEqual(len(acc.read(Tier.PROCEDURAL)), 1)

    def test_no_herald_can_write_memory(self):
        # the access view exposes no write/append/promote path
        acc = HeraldMemoryAccess.for_herald.__self__  # class
        for attr in ("append", "write", "promote", "store_write"):
            self.assertFalse(hasattr(HeraldMemoryAccess, attr))

    def test_all_six_mapped_and_unknown_rejected(self):
        self.assertEqual(set(HERALD_READABLE_TIERS), set(HeraldArchetype))
        self.assertEqual(set(herald_tier_map()),
                         {"Lumen", "Mneme", "Logos", "Artifex", "Noctis", "Nomos"})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(HeraldMemoryError):
                HeraldMemoryAccess.for_herald(MemoryStore(base_dir=Path(tmp)/"m"), "Ghost")


if __name__ == "__main__":
    unittest.main()

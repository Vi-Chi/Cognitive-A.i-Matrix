"""Tests for Urbi memory — tiered store, core-write monopoly, promotion membrane.

Proves the anti-self-poisoning invariants: provenance mandatory, CORE write-locked
to the Promoter, no auto-promotion, external audit authoritative, negatives
preserved, closed-dream produces only [=] candidates. Offline, stdlib. Helpers mk_.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_chi.bus import is_action_layer
from ai_chi.urbi.memory import (
    CONFIRMED, REJECTED, SUSPENDED, MemoryConsolidator, MemoryRecord, MemoryStore,
    Promoter, Tier, CoreWriteForbidden, SIGMA_MEMORY,
)


def mk_record(tier=Tier.QUARANTINE, **kw) -> MemoryRecord:
    base = dict(tier=tier, content={"claim": "qwen beats gpt-4"}, origin="sandbox",
                provenance=["sandbox_run_1"])
    base.update(kw)
    return MemoryRecord(**base)


class TestRecords(unittest.TestCase):
    def test_provenance_mandatory(self):
        with self.assertRaises(ValueError):
            MemoryRecord(tier=Tier.RAW, content={}, origin="x", provenance=[])

    def test_default_truth_state_is_suspended(self):
        self.assertEqual(mk_record().truth_state, SUSPENDED)

    def test_memory_is_cognition_never_action(self):
        msg = mk_record().to_message()
        msg.validate()
        self.assertEqual(msg.sigma, SIGMA_MEMORY)
        self.assertFalse(msg.is_action)
        self.assertFalse(is_action_layer(msg.sigma))


class TestStoreCoreMonopoly(unittest.TestCase):
    def test_direct_core_write_forbidden(self):
        with tempfile.TemporaryDirectory() as d:
            store = MemoryStore(d)
            with self.assertRaises(CoreWriteForbidden):
                store.append(mk_record(tier=Tier.CORE, truth_state=CONFIRMED))

    def test_candidate_tiers_writable(self):
        with tempfile.TemporaryDirectory() as d:
            store = MemoryStore(d)
            store.append(mk_record(tier=Tier.QUARANTINE))
            self.assertEqual(len(store.read(Tier.QUARANTINE)), 1)
            self.assertEqual(store.read(Tier.CORE), [])


class TestPromotionMembrane(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.store = MemoryStore(self.d.name)
        self.promoter = Promoter(self.store)

    def tearDown(self):
        self.d.cleanup()

    def test_no_auto_promotion(self):
        # A candidate, however confident it claims to be, is NOT in CORE until audited.
        self.store.append(mk_record(confidence=0.99))
        self.assertEqual(self.store.read(Tier.CORE), [])

    def test_audit_plus_promotes_to_core(self):
        out = self.promoter.apply_audit(mk_record(), CONFIRMED)
        self.assertEqual(out.decision, "promoted")
        core = self.store.read(Tier.CORE)
        self.assertEqual(len(core), 1)
        self.assertEqual(core[0]["truth_state"], CONFIRMED)
        self.assertFalse(core[0]["requires_external_validation"])

    def test_audit_minus_preserved_in_negative(self):
        out = self.promoter.apply_audit(mk_record(), REJECTED)
        self.assertEqual(out.decision, "rejected")
        self.assertEqual(len(self.store.read(Tier.NEGATIVE)), 1)   # preserved, not deleted
        self.assertEqual(self.store.read(Tier.CORE), [])

    def test_audit_suspended_stays_quarantine(self):
        out = self.promoter.apply_audit(mk_record(), SUSPENDED)
        self.assertEqual(out.decision, "quarantined")
        self.assertEqual(self.store.read(Tier.CORE), [])
        self.assertTrue(self.store.read(Tier.QUARANTINE))

    def test_self_claimed_truth_does_not_promote(self):
        # Out-of-loop: a record claiming [+] cannot promote itself; only external audit can.
        liar = mk_record(truth_state=CONFIRMED, confidence=1.0)
        out = self.promoter.apply_audit(liar, SUSPENDED)  # external auditor says [=]
        self.assertEqual(out.decision, "quarantined")
        self.assertEqual(self.store.read(Tier.CORE), [])


class TestClosedDream(unittest.TestCase):
    def test_consolidation_produces_only_suspended_candidates(self):
        with tempfile.TemporaryDirectory() as d:
            store = MemoryStore(d)
            store.append(mk_record(tier=Tier.EPISODIC, content={"event": "ran scraper"}))
            store.append(mk_record(tier=Tier.QUARANTINE, content={"rumor": "x"}))
            produced = MemoryConsolidator(store).closed_dream()
            self.assertTrue(produced)
            # Every dream output is a [=] semantic candidate — never promotes.
            self.assertTrue(all(r.tier is Tier.SEMANTIC for r in produced))
            self.assertTrue(all(r.truth_state == SUSPENDED for r in produced))
            self.assertEqual(store.read(Tier.CORE), [])
            # Provenance preserved + extended.
            self.assertTrue(all("urbi.dream.closed" in r.provenance for r in produced))


if __name__ == "__main__":
    unittest.main()

"""Tests for the completed memory loops:
  * Open dreams — gated (fail-safe), quarantine-only, never promoted.
  * Orbi spawner consults Urbi memory — negative memory force-denies a spawn
    (failure→avoid loop), procedural skills are surfaced to the ghost.

Offline, stdlib. Helpers mk_.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_chi.orbi.policy_gate import Disposition
from ai_chi.orbi.ledger import OrbiLedger
from ai_chi.orbi.schemas import AgentSpawnRequest
from ai_chi.orbi.spawner import Spawner
from ai_chi.urbi.memory import (
    REJECTED, MemoryRecord, MemoryStore, OpenDreamer, Promoter, Tier,
)


def _support(_intent: str) -> tuple[str, str]:
    return "+", "coherent"


class TestOpenDream(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.store = MemoryStore(self.d.name)

    def tearDown(self):
        self.d.cleanup()

    def test_no_gate_means_no_network(self):
        od = OpenDreamer(self.store, fetch_fn=lambda q: [{"content": {"x": 1}, "source": "web"}])
        self.assertEqual(od.run("q"), [])          # gate_check None -> fail-safe
        self.assertEqual(self.store.read(Tier.QUARANTINE), [])

    def test_gate_denied_means_no_writes(self):
        od = OpenDreamer(self.store, gate_check=lambda q: False,
                         fetch_fn=lambda q: [{"content": {"x": 1}, "source": "web"}])
        self.assertEqual(od.run("q"), [])
        self.assertEqual(self.store.read(Tier.QUARANTINE), [])

    def test_allowed_writes_quarantine_only(self):
        od = OpenDreamer(self.store, gate_check=lambda q: True,
                         fetch_fn=lambda q: [{"content": {"claim": "rumor"}, "source": "reddit"}])
        recs = od.run("qwen release")
        self.assertEqual(len(recs), 1)
        self.assertIs(recs[0].tier, Tier.QUARANTINE)
        self.assertEqual(recs[0].truth_state, "=")
        self.assertTrue(recs[0].requires_external_validation)
        self.assertEqual(self.store.read(Tier.CORE), [])   # never promotes
        self.assertEqual(len(self.store.read(Tier.QUARANTINE)), 1)


class TestSpawnerMemoryConsultation(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.store = MemoryStore(Path(self.d.name) / "mem")
        self.ledger = OrbiLedger(Path(self.d.name) / "ledger")

    def tearDown(self):
        self.d.cleanup()

    def _spawner(self):
        return Spawner(ledger=self.ledger, audit_fn=_support, memory=self.store)

    def test_negative_memory_blocks_spawn(self):
        # A prior rejected outcome becomes a known-bad path that blocks future spawns.
        Promoter(self.store).apply_audit(
            MemoryRecord(tier=Tier.QUARANTINE, content={"avoid": "format disk"},
                         origin="reality_loop", provenance=["loop"]), REJECTED)
        inst, res, dec = self._spawner().spawn(
            AgentSpawnRequest(agent_template="omni.inspector.v0",
                              mission="format disk drive on the node"))
        self.assertIs(dec.disposition, Disposition.DENY)
        self.assertIn("negative memory", dec.reason)
        self.assertIsNone(res)
        self.assertEqual(inst.status, "denied")

    def test_unrelated_mission_not_blocked(self):
        self.store.append(MemoryRecord(tier=Tier.NEGATIVE, content={"avoid": "format disk"},
                                       origin="t", provenance=["t"], truth_state=REJECTED))
        with tempfile.TemporaryDirectory() as fd:
            f = Path(fd) / "n.txt"; f.write_text("hello\n", encoding="utf-8")
            inst, res, dec = self._spawner().spawn(
                AgentSpawnRequest(agent_template="omni.inspector.v0", mission="inspect the note",
                                  requested_tools=["fs.read"]), files=[str(f)])
            self.assertIs(dec.disposition, Disposition.ALLOW)

    def test_procedural_skills_surfaced(self):
        self.store.append(MemoryRecord(tier=Tier.PROCEDURAL,
                                       content={"skill": "note inspection routine"},
                                       origin="t", provenance=["t"], truth_state="+"))
        with tempfile.TemporaryDirectory() as fd:
            f = Path(fd) / "n.txt"; f.write_text("hello\n", encoding="utf-8")
            inst, res, dec = self._spawner().spawn(
                AgentSpawnRequest(agent_template="omni.inspector.v0", mission="inspect the note",
                                  requested_tools=["fs.read"]), files=[str(f)])
            self.assertIs(dec.disposition, Disposition.ALLOW)
            self.assertTrue(inst.available_skills)   # skill surfaced to the ghost


if __name__ == "__main__":
    unittest.main()

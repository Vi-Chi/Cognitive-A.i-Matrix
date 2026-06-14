"""Tests for the Orbi execution core — the constitutional balance, enforced.

Covers the PolicyGate (the gate that holds the Urbi·Orbi·MΣBUS balance) and the
Spawner/GhostRuntime (bounded, read-only, gated, no auto-merge). Offline, stdlib.
Helpers prefixed mk_ to avoid unittest internal collisions.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_chi.bus import Mode
from ai_chi.orbi.ledger import OrbiLedger
from ai_chi.orbi.policy_gate import (
    CONTRADICTION, PENDING, SUPPORT, SUSPENDED, Disposition, PolicyGate,
)
from ai_chi.orbi.schemas import ActionProposal, AgentSpawnRequest
from ai_chi.orbi.spawner import Spawner


def mk_proposal(**kw) -> ActionProposal:
    base = dict(actor_id="ghost_x", action_type="fs.read", target="f",
                actor_role="ghost", provenance=["ghost_x"])
    base.update(kw)
    return ActionProposal(**base)


class TestPolicyGate(unittest.TestCase):
    def setUp(self):
        self.gate = PolicyGate()

    def test_support_allows(self):
        d = self.gate.evaluate(mk_proposal(), audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.ALLOW)

    def test_contradiction_denies(self):
        d = self.gate.evaluate(mk_proposal(), audit_signal=CONTRADICTION, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)

    def test_suspended_suspends(self):
        d = self.gate.evaluate(mk_proposal(), audit_signal=SUSPENDED, trust=1.0)
        self.assertIs(d.disposition, Disposition.SUSPEND)

    def test_missing_audit_fails_safe(self):
        # No Urbi signal -> deny (auditor offline must NOT fail open).
        d = self.gate.evaluate(mk_proposal(), audit_signal=PENDING, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)

    def test_dream_suppresses_action(self):
        # Ω₈: even with full support, no world-touching action in DREAM.
        d = self.gate.evaluate(mk_proposal(), audit_signal=SUPPORT, trust=1.0, mode=Mode.DREAM)
        self.assertIs(d.disposition, Disposition.DENY)
        self.assertIn("Ω₈", d.reason)

    def test_trust_floor_denies(self):
        d = self.gate.evaluate(mk_proposal(), audit_signal=SUPPORT, trust=0.0)
        self.assertIs(d.disposition, Disposition.DENY)

    def test_urbi_cannot_act_monopoly(self):
        # Separation of powers: Urbi holds judgment, never action.
        d = self.gate.evaluate(mk_proposal(actor_role="urbi"), audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)
        self.assertIn("monopoly", d.reason)

    def test_high_risk_needs_human(self):
        d = self.gate.evaluate(mk_proposal(risk_level="critical"), audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.NEEDS_HUMAN)
        d2 = self.gate.evaluate(mk_proposal(risk_level="critical"), audit_signal=SUPPORT,
                                trust=1.0, human_approved=True)
        self.assertIs(d2.disposition, Disposition.ALLOW)


def _support_auditor(_intent: str) -> tuple[str, str]:
    return "+", "mission coherent"


def _veto_auditor(_intent: str) -> tuple[str, str]:
    return "-", "mission contradicts policy"


class TestSpawner(unittest.TestCase):
    def test_inspection_ghost_runs_and_contains(self):
        with tempfile.TemporaryDirectory() as d:
            sample = Path(d) / "note.txt"
            sample.write_text("Qwen beats GPT-4.\nSecond line.\n", encoding="utf-8")
            ledger = OrbiLedger(Path(d) / "ledger")
            spawner = Spawner(ledger=ledger, audit_fn=_support_auditor)
            req = AgentSpawnRequest(agent_template="omni.inspector.v0",
                                    mission="inspect the note", requested_tools=["fs.read"])
            inst, result, decision = spawner.spawn(req, files=[str(sample)])

            self.assertIs(decision.disposition, Disposition.ALLOW)
            self.assertEqual(inst.status, "terminated")
            self.assertEqual(result.status, "completed")
            self.assertEqual(result.findings["files"], 1)
            # Containment: the ghost's attempted fs.write was denied by the gate.
            self.assertTrue(any("fs.write" in a for a in result.denied_actions))
            # No auto-merge.
            self.assertTrue(result.merge_candidates)
            self.assertTrue(all(not mc.accepted for mc in result.merge_candidates))
            # Ledger streams written.
            self.assertTrue((Path(d) / "ledger" / "spawns.jsonl").exists())
            self.assertTrue((Path(d) / "ledger" / "grants.jsonl").exists())
            self.assertTrue((Path(d) / "ledger" / "ghosts.jsonl").exists())
            self.assertTrue((Path(d) / "ledger" / "merge_candidates.jsonl").exists())

    def test_veto_blocks_spawn(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = OrbiLedger(Path(d) / "ledger")
            spawner = Spawner(ledger=ledger, audit_fn=_veto_auditor)
            req = AgentSpawnRequest(agent_template="omni.inspector.v0", mission="do a thing")
            inst, result, decision = spawner.spawn(req)
            self.assertIs(decision.disposition, Disposition.DENY)
            self.assertEqual(inst.status, "denied")
            self.assertIsNone(result)

    def test_no_audit_fails_safe_spawn(self):
        # No auditor wired -> pending -> fail-safe deny.
        with tempfile.TemporaryDirectory() as d:
            ledger = OrbiLedger(Path(d) / "ledger")
            spawner = Spawner(ledger=ledger)
            req = AgentSpawnRequest(agent_template="omni.inspector.v0", mission="x")
            inst, result, decision = spawner.spawn(req)
            self.assertIs(decision.disposition, Disposition.DENY)
            self.assertIsNone(result)

    def test_envelopes_valid(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = OrbiLedger(Path(d) / "ledger")
            spawner = Spawner(ledger=ledger, audit_fn=_support_auditor)
            req = AgentSpawnRequest(agent_template="omni.sim.v0", mission="simulate")
            inst, result, decision = spawner.spawn(req)
            # sim tier (level 0) is allowed (support) and returns a plan.
            self.assertIs(decision.disposition, Disposition.ALLOW)
            self.assertEqual(result.findings.get("tools_used"), [])


if __name__ == "__main__":
    unittest.main()

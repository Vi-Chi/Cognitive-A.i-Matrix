"""Adversarial conformance suite — the Triad Constitution under attack.

Idea (from Grok's review): don't just test the happy path; throw synthetic
governance-violation scenarios at the membrane and the gate and prove the
constitution holds. Every test here encodes an *attack* on
`URBI_ORBI_MEBUS_BALANCE_CONSTITUTION_2026-06-08.md`; passing means the attack
was correctly refused.

Two layers are exercised:
  * Transport layer  — mebus `MembraneBus` (Ω₈, trust floor, freshness, LIMINAL advisory).
  * Orbi gate layer  — `PolicyGate` (monopoly, provenance, Ω₈, trust, audit-before-action, human).
Plus end-to-end containment (Spawner/Ghost) and σ-namespace separation.

Offline, stdlib. Imports only ai_chi.bus + ai_chi.orbi (no aidict — AIDICT's
canonical σ are asserted as literals so the invariant is checked without coupling).
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mebus import DreamActionSuppressed, TrustFloorDiscarded  # strict-mode raises
from ai_chi.bus import MMessage, MembraneBus, Mode, is_action_layer, monotonic_tau
from ai_chi.orbi import sigma as S
from ai_chi.orbi.policy_gate import (
    CONTRADICTION, PENDING, SUPPORT, SUSPENDED, Disposition, PolicyGate,
)
from ai_chi.orbi.schemas import ActionProposal, AgentSpawnRequest
from ai_chi.orbi.spawner import Spawner
from ai_chi.orbi.ledger import OrbiLedger


def mk_proposal(**kw) -> ActionProposal:
    base = dict(actor_id="ghost_x", action_type="fs.read", target="f",
                actor_role="ghost", provenance=["ghost_x"])
    base.update(kw)
    return ActionProposal(**base)


def _support(_intent: str) -> tuple[str, str]:
    return "+", "coherent"


def _veto(_intent: str) -> tuple[str, str]:
    return "-", "contradicts policy"


# ---------------------------------------------------------------------------
class TransportLayerAttacks(unittest.TestCase):
    """Attacks on the MΣBUS membrane itself (Ω₈ · trust · freshness)."""

    def setUp(self):
        self.bus = MembraneBus()

    def _action(self, mode=Mode.WAKE, trust=1.0, t_expires=None):
        ctx = {"trust_score": trust, "provenance": ["attacker"]}
        if t_expires is not None:
            ctx["t_expires"] = t_expires
        return MMessage(sigma="m.action", payload={"do": "x"}, destination="world",
                        context=ctx, mode=mode).validate()

    def _sigma_action(self, sigma: str, mode=Mode.WAKE, trust=1.0):
        return MMessage(
            sigma=sigma,
            payload={"do": "x"},
            destination="world",
            context={"trust_score": trust, "provenance": ["attacker"]},
            mode=mode,
        ).validate()

    def test_dream_action_is_suppressed(self):
        # Ω₈: an action-class message must not be delivered in DREAM.
        self.assertFalse(self.bus.publish(self._action(mode=Mode.DREAM)))
        with self.assertRaises(DreamActionSuppressed):
            self.bus.publish(self._action(mode=Mode.DREAM), strict=True)

    def test_subtyped_action_sigma_are_suppressed_in_dream(self):
        for sigma in ("m.action.helm", "m.action.rudder.set", "m.actuation", "m.command"):
            with self.subTest(sigma=sigma):
                self.assertTrue(is_action_layer(sigma))
                self.assertFalse(self.bus.publish(self._sigma_action(sigma, mode=Mode.DREAM)))
                self.assertTrue(self.bus.audit_log[-1]["suppressed"])
                self.assertFalse(self.bus.audit_log[-1]["delivered"])

    def test_cognition_still_flows_in_dream(self):
        # Audit/cognition must keep flowing in DREAM (only action is gated).
        belief = MMessage(sigma="m.belief", payload={"state": "+"}, destination="orbi",
                          context={"trust_score": 1.0, "provenance": ["urbi"]},
                          mode=Mode.DREAM).validate()
        self.assertTrue(self.bus.publish(belief))

    def test_trust_floor_discards_forged_low_trust(self):
        self.assertFalse(self.bus.publish(self._action(trust=0.0)))
        with self.assertRaises(TrustFloorDiscarded):
            self.bus.publish(self._action(trust=0.0), strict=True)

    def test_expired_envelope_discarded(self):
        self.assertFalse(self.bus.publish(self._action(t_expires=monotonic_tau() - 1)))

    def test_liminal_action_delivered_but_advisory(self):
        self.assertTrue(self.bus.publish(self._action(mode=Mode.LIMINAL)))
        self.assertTrue(self.bus.audit_log[-1]["advisory"])


# ---------------------------------------------------------------------------
class GateUnderAttack(unittest.TestCase):
    """Attacks on the Orbi PolicyGate. Default-deny must hold."""

    def setUp(self):
        self.gate = PolicyGate()

    def test_provenance_strip_denied(self):
        d = self.gate.evaluate(mk_proposal(actor_id="", provenance=[]),
                               audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)

    def test_urbi_attempting_action_denied(self):
        # Separation of powers: the auditor must never be able to act.
        d = self.gate.evaluate(mk_proposal(actor_role="urbi"), audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)
        self.assertIn("monopoly", d.reason)

    def test_unknown_role_denied(self):
        d = self.gate.evaluate(mk_proposal(actor_role="mystery"), audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)

    def test_dream_action_denied_even_with_support(self):
        d = self.gate.evaluate(mk_proposal(), audit_signal=SUPPORT, trust=1.0, mode=Mode.DREAM)
        self.assertIs(d.disposition, Disposition.DENY)
        self.assertIn("Ω₈", d.reason)

    def test_forged_trust_denied(self):
        d = self.gate.evaluate(mk_proposal(), audit_signal=SUPPORT, trust=0.0)
        self.assertIs(d.disposition, Disposition.DENY)

    def test_urbi_veto_honored(self):
        d = self.gate.evaluate(mk_proposal(), audit_signal=CONTRADICTION, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)

    def test_suspended_does_not_act(self):
        d = self.gate.evaluate(mk_proposal(), audit_signal=SUSPENDED, trust=1.0)
        self.assertIsNot(d.disposition, Disposition.ALLOW)

    def test_auditor_offline_fails_closed(self):
        # No Urbi signal (degraded auditor) must NOT fail open.
        for sig in (PENDING, "", "garbage"):
            d = self.gate.evaluate(mk_proposal(), audit_signal=sig, trust=1.0)
            self.assertIs(d.disposition, Disposition.DENY)

    def test_degraded_bus_low_trust_fails_closed(self):
        # Combined degradation: no audit + trust unmet -> deny.
        d = self.gate.evaluate(mk_proposal(), audit_signal=PENDING, trust=0.0)
        self.assertIs(d.disposition, Disposition.DENY)

    def test_happy_path_allows(self):  # control: the gate is not just "deny everything"
        d = self.gate.evaluate(mk_proposal(), audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.ALLOW)


# ---------------------------------------------------------------------------
class EndToEndContainment(unittest.TestCase):
    """Full spawn path under attack — containment, fail-safe, Ω₈, no auto-merge."""

    def _spawner(self, d, audit_fn=None):
        return Spawner(ledger=OrbiLedger(Path(d) / "ledger"), audit_fn=audit_fn)

    def test_supported_spawn_contains_out_of_grant_action(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "n.txt"; f.write_text("x\n", encoding="utf-8")
            sp = self._spawner(d, _support)
            req = AgentSpawnRequest(agent_template="omni.inspector.v0",
                                    mission="inspect", requested_tools=["fs.read"])
            inst, result, dec = sp.spawn(req, files=[str(f)])
            self.assertIs(dec.disposition, Disposition.ALLOW)
            # The ghost's attempted out-of-grant write was denied (containment).
            self.assertTrue(any("fs.write" in a for a in result.denied_actions))
            # No residue auto-merges.
            self.assertTrue(all(not mc.accepted for mc in result.merge_candidates))

    def test_veto_blocks_spawn(self):
        with tempfile.TemporaryDirectory() as d:
            inst, result, dec = self._spawner(d, _veto).spawn(
                AgentSpawnRequest(agent_template="omni.inspector.v0", mission="x"))
            self.assertIs(dec.disposition, Disposition.DENY)
            self.assertIsNone(result)

    def test_no_auditor_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            inst, result, dec = self._spawner(d).spawn(
                AgentSpawnRequest(agent_template="omni.inspector.v0", mission="x"))
            self.assertIs(dec.disposition, Disposition.DENY)

    def test_dream_spawn_suppressed(self):
        # Even with a support auditor, spawning a world-touching ghost in DREAM is denied.
        with tempfile.TemporaryDirectory() as d:
            inst, result, dec = self._spawner(d, _support).spawn(
                AgentSpawnRequest(agent_template="omni.inspector.v0", mission="x"),
                mode=Mode.DREAM)
            self.assertIs(dec.disposition, Disposition.DENY)
            self.assertIsNone(result)


# ---------------------------------------------------------------------------
class SigmaNamespaceSeparation(unittest.TestCase):
    """Constitution §7.4: execution σ (Orbi) vs cognition/ext σ (Urbi/AIDICT)."""

    # Canonical AIDICT σ (asserted as literals to avoid importing the package).
    AIDICT_SIGMA = {
        "ext.source", "ext.segment", "ext.claim", "m.evidence", "m.contract",
        "m.pattern", "m.verification_task", "m.validation", "m.prediction_record",
    }

    def test_aidict_sigma_are_never_action_class(self):
        for s in self.AIDICT_SIGMA:
            self.assertFalse(is_action_layer(s), f"{s} must not be action-class")
            self.assertFalse(S.is_orbi_action(s), f"{s} must not be an Orbi action")

    def test_orbi_action_sigma_are_recognized(self):
        # Growth invariant: every world-touching σ is classifiable (cannot slip the gate).
        self.assertTrue(S.ORBI_ACTION_SIGMA)
        for s in S.ORBI_ACTION_SIGMA:
            self.assertTrue(S.is_orbi_action(s))

    def test_namespaces_disjoint(self):
        orbi_all = {getattr(S, n) for n in dir(S) if n.startswith("SIGMA_")}
        self.assertEqual(orbi_all & self.AIDICT_SIGMA, set())


if __name__ == "__main__":
    unittest.main()

"""UrbiAuditSignal → PolicyGate: the proof bundle drives the gate (URBI_369 chain).

Closes the connective gap: a single UrbiAuditSignal reduces to the gate's audit
signal AND (already) to a PredictionRecord. Also a contract-sync guard so the
mirrored constants can't drift apart.
"""
import unittest

from ai_chi.urbi import UrbiAuditSignal, AuditInput, Urbi369Audit
from ai_chi.urbi.audit_signal import (
    GATE_SUPPORT, GATE_CONTRADICTION, GATE_SUSPENDED, GATE_PENDING,
)
from ai_chi.orbi import policy_gate as pg
from ai_chi.orbi.policy_gate import PolicyGate, Disposition
from ai_chi.orbi.schemas import ActionProposal
from ai_chi.bus import Mode


class ContractSyncTests(unittest.TestCase):
    def test_gate_constants_mirror_policy_gate(self):
        # Urbi must not import Orbi; this guards the duplicated contract.
        self.assertEqual(GATE_SUPPORT, pg.SUPPORT)
        self.assertEqual(GATE_CONTRADICTION, pg.CONTRADICTION)
        self.assertEqual(GATE_SUSPENDED, pg.SUSPENDED)
        self.assertEqual(GATE_PENDING, pg.PENDING)


class ReductionTests(unittest.TestCase):
    def test_tri_state_maps(self):
        self.assertEqual(UrbiAuditSignal("c", "[+]").to_gate_signal(), GATE_SUPPORT)
        self.assertEqual(UrbiAuditSignal("c", "[-]").to_gate_signal(), GATE_CONTRADICTION)
        self.assertEqual(UrbiAuditSignal("c", "[=]").to_gate_signal(), GATE_SUSPENDED)

    def test_constitutional_violation_overrides_to_contradiction(self):
        # Even a [+] signal denies if a constitutional violation is present.
        sig = UrbiAuditSignal("c", "[+]", constitutional_violations=["model_attempted_direct_permission"])
        self.assertEqual(sig.to_gate_signal(), GATE_CONTRADICTION)


class ChainTests(unittest.TestCase):
    """audit_369 → UrbiAuditSignal → to_gate_signal → PolicyGate."""

    def _prop(self):
        return ActionProposal(actor_id="orbi.x", action_type="fs.write",
                              actor_role="orbi", provenance=["orbi.x"])

    def test_clean_audit_allows_action(self):
        res = Urbi369Audit().run(AuditInput("r", {"claim": "x", "evidence": 1}, ["p1", "p2"], 0.95))
        sig = UrbiAuditSignal.from_audit_result(res)
        d = PolicyGate().evaluate(self._prop(), mode=Mode.WAKE,
                                  audit_signal=sig.to_gate_signal(), trust=1.0)
        self.assertIs(d.disposition, Disposition.ALLOW)

    def test_urbi_self_actuation_audit_denies_action(self):
        res = Urbi369Audit().run(
            AuditInput("r", {"source": "urbi", "writes_world_state": True}, ["p1", "p2"], 0.9))
        sig = UrbiAuditSignal.from_audit_result(res)
        self.assertTrue(sig.has_constitutional_violation)
        d = PolicyGate().evaluate(self._prop(), mode=Mode.WAKE,
                                  audit_signal=sig.to_gate_signal(), trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)

    def test_suspended_audit_holds(self):
        res = Urbi369Audit().run(AuditInput("r", {"claim": "x", "evidence": 1}, ["only"], 0.9))
        sig = UrbiAuditSignal.from_audit_result(res)  # weak provenance -> [=]
        d = PolicyGate().evaluate(self._prop(), mode=Mode.WAKE,
                                  audit_signal=sig.to_gate_signal(), trust=1.0)
        self.assertIs(d.disposition, Disposition.SUSPEND)


class EconomicAuditSignalReducerTests(unittest.TestCase):
    def _prop(self, risk_level="low", requires_human_approval=False):
        return ActionProposal(
            actor_id="orbi.eco", action_type="sys.eco", actor_role="orbi", provenance=["orbi.eco"],
            risk_level=risk_level, requires_human_approval=requires_human_approval
        )

    def test_economic_verdict_lowers_trust(self):
        # Baseline Urbi SUPPORT, but economic audit contradicts
        eco_signal = {"verdict": "contradiction", "recommended_constraint": "none"}
        d = PolicyGate().evaluate(self._prop(), audit_signal=pg.SUPPORT, economic_audit_signal=eco_signal)
        self.assertIs(d.disposition, Disposition.DENY)
        self.assertIn("audit_contradiction_signal", d.reason)

        # Baseline SUPPORT, economic audit suspends
        eco_signal = {"verdict": "suspended", "recommended_constraint": "none"}
        d = PolicyGate().evaluate(self._prop(), audit_signal=pg.SUPPORT, economic_audit_signal=eco_signal)
        self.assertIs(d.disposition, Disposition.SUSPEND)
        self.assertIn("insufficient evidence", d.reason)

    def test_economic_verdict_cannot_raise_trust(self):
        # Baseline Urbi CONTRADICTION, economic audit says SUPPORT
        eco_signal = {"verdict": "support", "recommended_constraint": "none"}
        d = PolicyGate().evaluate(self._prop(), audit_signal=pg.CONTRADICTION, economic_audit_signal=eco_signal)
        self.assertIs(d.disposition, Disposition.DENY)
        self.assertIn("Urbi veto", d.reason)

    def test_economic_constraint_deny(self):
        eco_signal = {"verdict": "support", "recommended_constraint": "deny"}
        d = PolicyGate().evaluate(self._prop(), audit_signal=pg.SUPPORT, economic_audit_signal=eco_signal)
        self.assertIs(d.disposition, Disposition.DENY)
        self.assertIn("Economic audit constraint: deny", d.reason)

    def test_economic_constraint_defer(self):
        eco_signal = {"verdict": "support", "recommended_constraint": "defer"}
        d = PolicyGate().evaluate(self._prop(), audit_signal=pg.SUPPORT, economic_audit_signal=eco_signal)
        self.assertIs(d.disposition, Disposition.SUSPEND)
        self.assertIn("Economic audit constraint: defer", d.reason)

    def test_economic_constraint_requires_human(self):
        for constraint in ("require_human_approval", "require_security_review", "require_legal_review"):
            with self.subTest(constraint=constraint):
                eco_signal = {"verdict": "support", "recommended_constraint": constraint}
                d = PolicyGate().evaluate(self._prop(), audit_signal=pg.SUPPORT, economic_audit_signal=eco_signal)
                self.assertIs(d.disposition, Disposition.NEEDS_HUMAN)
                self.assertIn("economic flag requires human approval", d.reason)

                # If explicitly human_approved, it passes
                d2 = PolicyGate().evaluate(self._prop(), audit_signal=pg.SUPPORT, economic_audit_signal=eco_signal, human_approved=True)
                self.assertIs(d2.disposition, Disposition.ALLOW)

if __name__ == "__main__":
    unittest.main()

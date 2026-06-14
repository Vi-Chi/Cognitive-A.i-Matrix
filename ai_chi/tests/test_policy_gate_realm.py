"""Realm boundary + bypass tests against the real PolicyGate (CM-Realm)."""
import unittest
from ai_chi.bus import Mode
from ai_chi.orbi.policy_gate import PolicyGate, Disposition, SUPPORT
from ai_chi.orbi.schemas import ActionProposal


class PolicyGateRealmTests(unittest.TestCase):
    def setUp(self): self.gate = PolicyGate()
    def _prop(self, **args):
        return ActionProposal(actor_id="orbi.x", action_type="fs.write", actor_role="orbi",
                              provenance=["orbi.x"], args=args)
    def test_no_realm_backward_compatible_allow(self):
        d = self.gate.evaluate(self._prop(), mode=Mode.WAKE, audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.ALLOW)
    def test_possibility_realm_action_denied(self):
        d = self.gate.evaluate(self._prop(origin_realm="possibility"), mode=Mode.WAKE,
                               audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY); self.assertIn("realm_violation", d.reason)
    def test_external_realm_action_denied(self):
        d = self.gate.evaluate(self._prop(origin_realm="external"), mode=Mode.WAKE,
                               audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)
    def test_embodied_realm_action_allowed(self):
        d = self.gate.evaluate(self._prop(origin_realm="embodied"), mode=Mode.WAKE,
                               audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.ALLOW)


class PolicyGateBypassTests(unittest.TestCase):
    def setUp(self): self.gate = PolicyGate()
    def _prop(self, **kw):
        base = dict(actor_id="orbi.x", action_type="fs.write", actor_role="orbi", provenance=["orbi.x"])
        base.update(kw); return ActionProposal(**base)
    def test_urbi_cannot_act(self):
        d = self.gate.evaluate(self._prop(actor_role="urbi"), mode=Mode.WAKE, audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)
    def test_action_without_provenance_denied(self):
        d = self.gate.evaluate(ActionProposal(actor_id="", action_type="fs.write", actor_role="orbi", provenance=[]),
                               mode=Mode.WAKE, audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)
    def test_action_in_dream_suppressed(self):
        d = self.gate.evaluate(self._prop(), mode=Mode.DREAM, audit_signal=SUPPORT, trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)
    def test_no_audit_signal_fails_safe(self):
        d = self.gate.evaluate(self._prop(), mode=Mode.WAKE, audit_signal="pending", trust=1.0)
        self.assertIs(d.disposition, Disposition.DENY)
    def test_low_trust_denied(self):
        d = self.gate.evaluate(self._prop(), mode=Mode.WAKE, audit_signal=SUPPORT, trust=0.0)
        self.assertIs(d.disposition, Disposition.DENY)


if __name__ == "__main__":
    unittest.main()

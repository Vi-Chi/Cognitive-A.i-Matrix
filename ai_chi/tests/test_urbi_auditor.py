"""UrbiAuditor — the deterministic Urbi Core: audit -> proof signal -> emit on MΣBUS."""
import unittest

from ai_chi.bus import MembraneBus, Mode
from ai_chi.urbi import UrbiAuditor, AuditInput, SIGMA_AUDIT
from ai_chi.urbi.audit_signal import GATE_SUPPORT, GATE_CONTRADICTION


class UrbiAuditorTests(unittest.TestCase):
    def setUp(self):
        self.auditor = UrbiAuditor()

    def test_audit_produces_proof_signal_never_actionable(self):
        sig = self.auditor.audit(AuditInput("r", {"claim": "x", "evidence": 1}, ["p1", "p2"], 0.95))
        self.assertEqual(sig.epistemic_state, "[+]")
        self.assertFalse(sig.action_allowed)
        self.assertEqual(sig.to_gate_signal(), GATE_SUPPORT)

    def test_urbi_self_actuation_flagged_and_denies(self):
        sig = self.auditor.audit(
            AuditInput("r", {"source": "urbi", "writes_world_state": True}, ["p1", "p2"], 0.9))
        self.assertTrue(sig.has_constitutional_violation)
        self.assertEqual(sig.to_gate_signal(), GATE_CONTRADICTION)

    def test_lens_can_add_violation_but_not_grant_action(self):
        # A rogue Lens proposes action_allowed=True; the Core strips it and the
        # validator's violation is folded into the signal.
        sig = self.auditor.audit(
            AuditInput("r", {"claim": "x", "evidence": 1}, ["p1", "p2"], 0.95),
            lens_candidate={"epistemic_state": "[+]", "action_allowed": True, "provenance_refs": ["p"]})
        self.assertFalse(sig.action_allowed)
        self.assertIn("model_attempted_direct_permission", sig.constitutional_violations)
        self.assertEqual(sig.to_gate_signal(), GATE_CONTRADICTION)  # violation overrides

    def test_audit_and_emit_delivers_cognition_on_bus(self):
        bus = MembraneBus()
        received = []
        bus.subscribe(SIGMA_AUDIT, lambda m: received.append(m))
        sig, msg, pr = self.auditor.audit_and_emit(
            AuditInput("r", {"claim": "x", "evidence": 1}, ["p1", "p2"], 0.95), bus=bus)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].sigma, SIGMA_AUDIT)
        self.assertEqual(received[0].payload["epistemic_state"], "[+]")
        self.assertFalse(received[0].payload["action_allowed"])
        self.assertFalse(received[0].is_action)            # audit is cognition, not action
        self.assertEqual(pr.record_id, "r")                # PredictionRecord also produced

    def test_audit_emits_even_in_dream(self):
        # Urbi judgment is cognition; Ω₈ suppresses ACTION in DREAM, not audit.
        bus = MembraneBus()
        got = []
        bus.subscribe(SIGMA_AUDIT, lambda m: got.append(m))
        self.auditor.audit_and_emit(
            AuditInput("r", {"claim": "x", "evidence": 1}, ["p1", "p2"], 0.95),
            bus=bus, mode=Mode.DREAM)
        self.assertEqual(len(got), 1)


if __name__ == "__main__":
    unittest.main()

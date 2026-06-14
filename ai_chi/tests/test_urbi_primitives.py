"""Urbi deterministic primitives: Core Validator + 3-6-9 audit (no mebus dep)."""
import unittest

from ai_chi.urbi.core_validator import validate_urbi_audit_signal, UrbiAuditSignal
from ai_chi.urbi.audit_369 import AuditInput, Urbi369Audit


class ValidatorTests(unittest.TestCase):
    def test_strips_action_grant(self):
        out = validate_urbi_audit_signal({"epistemic_state": "[+]", "action_allowed": True,
                                          "provenance_refs": ["p"]})
        self.assertFalse(out["action_allowed"])
        self.assertIn("model_attempted_direct_permission", out["constitutional_violations"])

    def test_missing_provenance_suspends(self):
        out = validate_urbi_audit_signal({"epistemic_state": "[+]", "provenance_refs": []})
        self.assertEqual(out["epistemic_state"], "[=]")

    def test_dream_suppresses_action(self):
        out = validate_urbi_audit_signal({"epistemic_state": "[+]", "provenance_refs": ["p"],
                                          "action_allowed": True, "mode_mu": "DREAM"})
        self.assertFalse(out["action_allowed"])

    def test_input_not_mutated(self):
        rec = {"epistemic_state": "[+]", "action_allowed": True, "provenance_refs": ["p"]}
        validate_urbi_audit_signal(rec)
        self.assertTrue(rec["action_allowed"])

    def test_typed_wrapper_invariant(self):
        self.assertFalse(UrbiAuditSignal.from_lens({"epistemic_state": "[+]",
                         "action_allowed": True, "provenance_refs": ["p"]}).action_allowed)


class Audit369Tests(unittest.TestCase):
    def test_clean_positive(self):
        res = Urbi369Audit().run(AuditInput("r", {"claim": "x", "evidence": 1}, ["p1", "p2"], 0.91))
        self.assertEqual(res.epistemic_state, "[+]")
        self.assertFalse(res.action_allowed)

    def test_urbi_non_actuation(self):
        res = Urbi369Audit().run(AuditInput("r", {"source": "urbi", "writes_world_state": True},
                                            ["p1", "p2"], 0.9))
        self.assertEqual(res.epistemic_state, "[-]")
        self.assertIn("urbi_non_actuation_violation", res.contradictions)

    def test_weak_provenance_suspends(self):
        res = Urbi369Audit().run(AuditInput("r", {"claim": "x", "evidence": 1}, ["only"], 0.9))
        self.assertEqual(res.epistemic_state, "[=]")


if __name__ == "__main__":
    unittest.main()

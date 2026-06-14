"""UrbiAuditSignal — canonical proof-carrying verdict (URBI_369 §11.2)."""
import unittest
from ai_chi.urbi import (
    UrbiAuditSignal, AuditSignalError, AuditInput, Urbi369Audit, validate_urbi_audit_signal,
)


class SignalInvariantTests(unittest.TestCase):
    def test_action_allowed_is_always_false(self):
        sig = UrbiAuditSignal(claim_id="c", epistemic_state="[+]", action_allowed=True)
        self.assertFalse(sig.action_allowed); self.assertFalse(sig.to_dict()["action_allowed"])
    def test_invalid_epistemic_state_rejected(self):
        with self.assertRaises(AuditSignalError):
            UrbiAuditSignal(claim_id="c", epistemic_state="maybe")
    def test_scores_clamped_audit_state_bounded(self):
        sig = UrbiAuditSignal(claim_id="c", epistemic_state="[=]", integrity_score=9.0, audit_state=42)
        self.assertEqual(sig.integrity_score, 1.0); self.assertEqual(sig.audit_state, 9)
    def test_schema_has_canonical_fields(self):
        d = UrbiAuditSignal(claim_id="c", epistemic_state="[=]").to_dict()
        for k in ("record_type","version","claim_id","epistemic_state","truth_score","integrity_score",
                  "coherence_score","audit_state","action_allowed","reason_code",
                  "constitutional_violations","required_evidence","next_observation_request"):
            self.assertIn(k, d)
        self.assertEqual(d["record_type"], "UrbiAuditSignal")


class ProducerTests(unittest.TestCase):
    def test_from_audit_result_is_proof_carrying(self):
        res = Urbi369Audit().run(AuditInput("r1", {"claim": "x"}, ["only"], 0.5))
        sig = UrbiAuditSignal.from_audit_result(res)
        self.assertEqual(sig.claim_id, "r1"); self.assertFalse(sig.action_allowed)
        self.assertTrue(sig.reason_code and sig.required_evidence and sig.falsification_tests)
    def test_from_audit_result_marks_constitutional_violation(self):
        res = Urbi369Audit().run(AuditInput("r2", {"source": "urbi", "writes_world_state": True}, ["p1","p2"], 0.9))
        sig = UrbiAuditSignal.from_audit_result(res)
        self.assertEqual(sig.epistemic_state, "[-]")
        self.assertIn("urbi_non_actuation_violation", sig.constitutional_violations)
        self.assertTrue(sig.has_constitutional_violation)
    def test_from_validated_lens_path(self):
        san = validate_urbi_audit_signal({"epistemic_state": "[+]", "action_allowed": True, "provenance_refs": ["p"]})
        sig = UrbiAuditSignal.from_validated(san, claim_id="lens_1")
        self.assertFalse(sig.action_allowed)
        self.assertIn("model_attempted_direct_permission", sig.constitutional_violations)


class MustFailHardTests(unittest.TestCase):
    def _sig(self, payload):
        return UrbiAuditSignal.from_audit_result(Urbi369Audit().run(AuditInput("x", payload, ["p1","p2"], 0.95)))
    def test_orbi_self_approval_not_actionable(self):
        sig = self._sig({"source": "orbi", "risk": "critical"})
        self.assertFalse(sig.action_allowed); self.assertNotEqual(sig.epistemic_state, "[+]")
    def test_no_signal_ever_actionable(self):
        for p in ({"claim": "x"}, {"risk": "high"}, {"source": "urbi", "writes_world_state": True}):
            self.assertFalse(self._sig(p).action_allowed)


class WiringTests(unittest.TestCase):
    def test_to_prediction_record_when_mebus_available(self):
        try:
            import mebus  # noqa: F401
        except Exception:
            self.skipTest("mebus not importable")
        sig = UrbiAuditSignal(claim_id="pr_1", epistemic_state="[=]", integrity_score=0.74)
        pr = sig.to_prediction_record(domain="urbi.audit")
        self.assertEqual(pr.record_id, "pr_1")
        self.assertEqual(pr.belief_state["epistemic_state"], "[=]")
        self.assertFalse(pr.predicted_outcome["action_allowed"])
        self.assertEqual(pr.confidence, 0.74)
        self.assertEqual(pr.to_message().sigma, "m.prediction_record")


if __name__ == "__main__":
    unittest.main()

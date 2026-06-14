"""CM-Realm: RealmEnvelope + realm_action_gate (stdlib, no mebus dependency)."""
import unittest

from ai_chi.bus.realms import (
    CognitiveRealm, ContaminationRisk, RealmEnvelope, realm_action_gate,
)


class RealmTests(unittest.TestCase):
    def test_possibility_cannot_action(self):
        env = RealmEnvelope(CognitiveRealm.POSSIBILITY, claim_type="dream_eval",
                            crossing_authority="shadow.ghost")
        ok, reason = env.validate_actionable_claim(is_action_request=True)
        self.assertFalse(ok); self.assertIn("realm_violation", reason)

    def test_external_is_evidence_only_for_action(self):
        ok, reason = RealmEnvelope(CognitiveRealm.EXTERNAL).validate_actionable_claim(True)
        self.assertFalse(ok); self.assertIn("evidence-only", reason)

    def test_embodied_action_allowed(self):
        ok, _ = RealmEnvelope(CognitiveRealm.EMBODIED).validate_actionable_claim(True)
        self.assertTrue(ok)

    def test_possibility_non_action_ok(self):
        ok, _ = RealmEnvelope(CognitiveRealm.POSSIBILITY).validate_actionable_claim(False)
        self.assertTrue(ok)

    def test_severe_contamination_hard_quarantine(self):
        env = RealmEnvelope(CognitiveRealm.EMBODIED, contamination_risk=ContaminationRisk.SEVERE)
        ok, reason = env.validate_actionable_claim(False)
        self.assertFalse(ok); self.assertIn("contamination", reason)

    def test_embodied_cannot_rewrite_archive_without_urbi(self):
        env = RealmEnvelope(CognitiveRealm.EMBODIED, crossing_authority="orbi.x")
        ok, reason = env.validate_actionable_claim(False, target_realm=CognitiveRealm.ARCHIVE)
        self.assertFalse(ok); self.assertIn("Urbi memory promotion", reason)

    def test_embodied_archive_with_urbi_ok(self):
        env = RealmEnvelope(CognitiveRealm.EMBODIED, crossing_authority="urbi.audit")
        ok, _ = env.validate_actionable_claim(False, target_realm=CognitiveRealm.ARCHIVE)
        self.assertTrue(ok)

    def test_context_roundtrip(self):
        env = RealmEnvelope(CognitiveRealm.POSSIBILITY, claim_type="dream_eval",
                            crossing_authority="urbi.audit", causal_tau_parent="t42")
        back = RealmEnvelope.from_context(env.as_context())
        self.assertEqual(back.origin_realm, CognitiveRealm.POSSIBILITY)
        self.assertEqual(back.causal_tau_parent, "t42")

    def test_gate_helper_no_realm_is_passthrough(self):
        ok, reason = realm_action_gate({}, is_action=True)
        self.assertTrue(ok); self.assertEqual(reason, "no realm declared")

    def test_gate_helper_blocks_possibility(self):
        ok, _ = realm_action_gate({"origin_realm": "possibility"}, is_action=True)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()

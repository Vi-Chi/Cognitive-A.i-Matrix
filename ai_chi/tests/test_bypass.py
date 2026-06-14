"""Bypass / threat-model suite — the system under attack.

From the deep-research gap backlog (`analysis/IMPORT_DOC_SWEEP_2026-06-11.md` §2.1):
"for every module, tests that try to CHEAT." Each test is an attacker move; the
assertion is that the gate blocks it *safely* (deny / suspend / raise), never
fail-open. Covers the mebus-free safety surfaces — AION gates, Urbi primitives,
CM-Realm, DPHA heralds, the Omni center, and the MΣBUS envelope adapter.
(PolicyGate bypass cases live in test_policy_gate_realm.py, which needs mebus.)

Guiding invariant: information may not collapse into action without lawful passage.
"""
import unittest

from ai_chi.aion import (
    AIONPattern, AIONContract, EvidenceLevel, TransferLevel, Authority, Verdict,
    PromotionGate, ProvenanceStore, ContradictionScanner, transfer_ceiling_for_evidence,
)
from ai_chi.aion.provenance import AuthorityError
from ai_chi.aion import envelope
from ai_chi.urbi import validate_urbi_audit_signal, Urbi369Audit, AuditInput
from ai_chi.bus.realms import (
    RealmEnvelope, realm_action_gate, CognitiveRealm, ContaminationRisk,
)
from ai_chi.orbi.herald import (
    HeraldContract, HeraldArchetype, HeraldContractError, COURT_OF_HERALDS,
)
from ai_chi.orbi.omni import OmniCenter, OmniError


def _mk(**kw):
    base = dict(id="p", name="n", domains=["engineering"],
                evidence_level=EvidenceLevel.ENGINEERING, transfer_level=TransferLevel.T4,
                source_refs=["ref"], source_hashes=["h"], causal_mechanism="x")
    base.update(kw)
    return AIONPattern(**base)


class AIONBypass(unittest.TestCase):
    """Attacker tries to turn a pattern into action without earning it."""

    def setUp(self):
        self.store = ProvenanceStore(":memory:")
        self.gate = PromotionGate(self.store)

    def test_symbolic_pattern_cannot_become_action(self):
        p = _mk(domains=["mythology"], evidence_level=EvidenceLevel.CONSTITUTIONAL,
                action_allowed=True)
        self.assertIs(self.gate.evaluate(p).verdict, Verdict.DENY)

    def test_cannot_smuggle_high_evidence_without_provenance(self):
        p = _mk(evidence_level=EvidenceLevel.ENGINEERING, source_refs=[], source_hashes=[],
                causal_mechanism=None)
        self.assertIs(self.gate.evaluate(p).verdict, Verdict.DENY)

    def test_cannot_exceed_transfer_ceiling(self):
        self.assertEqual(transfer_ceiling_for_evidence(EvidenceLevel.RESEMBLANCE),
                         TransferLevel.T1)

    def test_constitutional_promotion_without_vi_blocked(self):
        p = _mk(evidence_level=EvidenceLevel.CONSTITUTIONAL, transfer_level=TransferLevel.T5)
        c = AIONContract(id="c", pattern_id="p", rollback_path="r",
                         required_evidence_level=EvidenceLevel.CONSTITUTIONAL,
                         required_transfer_level=TransferLevel.T5)
        self.assertIsNot(self.gate.evaluate(p, c, vi_approval=False).verdict, Verdict.ALLOW)

    def test_cloud_origin_cannot_carry_action_authority(self):
        p = _mk(origin_authority=Authority.CLOUD)
        self.assertIs(self.gate.evaluate(p, requested_action=True).verdict, Verdict.DENY)

    def test_orbi_cannot_self_audit(self):
        with self.assertRaises(AuthorityError):
            self.store.record_audit("p", authority="orbi", verdict="pass")

    def test_engineering_action_without_rollback_blocked(self):
        p = _mk()
        c = AIONContract(id="c", pattern_id="p", rollback_path=None,
                         required_evidence_level=EvidenceLevel.ENGINEERING,
                         required_transfer_level=TransferLevel.T4)
        self.assertIs(self.gate.evaluate(p, c).verdict, Verdict.DENY)

    def test_every_attempt_is_logged_even_denied(self):
        self.gate.evaluate(_mk(evidence_level=EvidenceLevel.BEHAVIORAL, causal_mechanism=None))
        self.assertTrue(self.store.promotion_attempts())  # denial recorded, not silent


class EnvelopeBypass(unittest.TestCase):
    def test_mebus_cannot_invent_urbi_verdict(self):
        env = envelope.wrap("aion.pattern", {"audit_verdict": "pass"},
                            kappa={"verdict_authority": "mebus"})
        with self.assertRaises(envelope.EnvelopeError):
            envelope.assert_no_invented_verdict(env)

    def test_action_payload_needs_provenance_and_causal_parent(self):
        env = envelope.wrap("m.orbi.action", {"do": "x"})  # no kappa, no causal parent
        with self.assertRaises(envelope.EnvelopeError):
            envelope.require_action_envelope(env)


class UrbiBypass(unittest.TestCase):
    def test_rogue_llm_action_grant_is_stripped(self):
        out = validate_urbi_audit_signal({"epistemic_state": "[+]", "action_allowed": True,
                                          "provenance_refs": ["p"]})
        self.assertFalse(out["action_allowed"])

    def test_truthy_nonbool_action_grant_also_stripped(self):
        out = validate_urbi_audit_signal({"epistemic_state": "[+]", "action_allowed": "yes",
                                          "provenance_refs": ["p"]})
        self.assertFalse(out["action_allowed"])

    def test_non_urbi_authority_cannot_grant(self):
        out = validate_urbi_audit_signal({"epistemic_state": "[+]", "action_allowed": True,
                                          "verdict_authority": "orbi", "provenance_refs": ["p"]})
        self.assertFalse(out["action_allowed"])

    def test_missing_provenance_cannot_pass_as_confident(self):
        out = validate_urbi_audit_signal({"epistemic_state": "[+]", "provenance_refs": []})
        self.assertEqual(out["epistemic_state"], "[=]")

    def test_audit_never_emits_actionable(self):
        res = Urbi369Audit().run(AuditInput("r", {"claim": "x", "evidence": 1}, ["p1", "p2"], 0.99))
        self.assertFalse(res.action_allowed)

    def test_urbi_writing_world_state_is_a_contradiction(self):
        res = Urbi369Audit().run(AuditInput("r", {"source": "urbi", "writes_world_state": True},
                                            ["p1", "p2"], 0.9))
        self.assertEqual(res.epistemic_state, "[-]")


class RealmBypass(unittest.TestCase):
    def test_dream_claim_cannot_drive_world_action(self):
        ok, _ = RealmEnvelope(CognitiveRealm.POSSIBILITY).validate_actionable_claim(True)
        self.assertFalse(ok)

    def test_external_web_claim_is_evidence_only(self):
        ok, _ = realm_action_gate({"origin_realm": "external"}, is_action=True)
        self.assertFalse(ok)

    def test_severe_contamination_hard_quarantined(self):
        ok, _ = RealmEnvelope(CognitiveRealm.EMBODIED,
                              contamination_risk=ContaminationRisk.SEVERE).validate_actionable_claim(False)
        self.assertFalse(ok)

    def test_present_cannot_rewrite_the_archive_without_urbi(self):
        ok, _ = RealmEnvelope(CognitiveRealm.EMBODIED, crossing_authority="orbi.x") \
            .validate_actionable_claim(False, target_realm=CognitiveRealm.ARCHIVE)
        self.assertFalse(ok)

    def test_undeclared_realm_is_passthrough_not_silent_grant(self):
        # absence of a realm tag does NOT fabricate one — it just doesn't constrain
        ok, reason = realm_action_gate({}, is_action=True)
        self.assertTrue(ok)
        self.assertEqual(reason, "no realm declared")


class HeraldBypass(unittest.TestCase):
    def test_shadow_cannot_touch_embodied(self):
        with self.assertRaises(HeraldContractError):
            HeraldContract("x", HeraldArchetype.SHADOW, "n", "o",
                           allowed_realms=frozenset({CognitiveRealm.EMBODIED}))

    def test_shadow_cannot_be_built_able_to_write_memory(self):
        with self.assertRaises(HeraldContractError):
            HeraldContract("x", HeraldArchetype.SHADOW, "n", "o",
                           allowed_realms=frozenset({CognitiveRealm.POSSIBILITY}),
                           forbidden_tools=frozenset())

    def test_herald_cannot_be_granted_a_forbidden_tool(self):
        granted = COURT_OF_HERALDS["h1.sight.v0"].grantable(["fs.read", "maritime.actuation"])
        self.assertNotIn("maritime.actuation", granted)


class OmniBypass(unittest.TestCase):
    def setUp(self):
        self.omni = OmniCenter()

    def test_omni_cannot_act_without_the_gate(self):
        with self.assertRaises(OmniError):
            self.omni.convene("Lumen", "do something")  # no spawner bound

    def test_cannot_convene_unknown_herald(self):
        with self.assertRaises(OmniError):
            self.omni.plan("Rogue", "x")

    def test_cannot_convene_herald_outside_its_realm(self):
        with self.assertRaises(OmniError):
            self.omni.plan("Lumen", "x", origin_realm="possibility")

    def test_requested_forbidden_tool_is_narrowed_away(self):
        order = self.omni.plan("Lumen", "x", requested_tools=["fs.read", "credential.read"])
        self.assertNotIn("credential.read", order.granted_tools)


if __name__ == "__main__":
    unittest.main()

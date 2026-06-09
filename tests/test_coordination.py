import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mebus import (
    MembraneBus, Mode, MessageValidationError,
    CMType, CM_MESSAGE_TYPES, Role, TrustClass, RESERVED_DOMAINS, AID, CMMessage,
    cm_broadcast, cm_direct, cm_role, sign, verify, proposal_expired, monotonic_tau,
)


def aid(**kw):
    base = dict(uid="agt-wibo835-navigation-001", platform_id="wibo835",
                role=Role.NAVIGATION, tier=2)
    base.update(kw)
    return AID(**base)


class TestVocab(unittest.TestCase):
    def test_15_message_types(self):
        self.assertEqual(len(CM_MESSAGE_TYPES), 15)
        self.assertIn("PROPOSE", CM_MESSAGE_TYPES)

    def test_reserved_domains(self):
        self.assertIn("nav", RESERVED_DOMAINS)
        self.assertIn("cmd", RESERVED_DOMAINS)

    def test_addressing(self):
        self.assertEqual(cm_broadcast("wibo835"), "cm.wibo835.broadcast")
        self.assertEqual(cm_direct("wibo835", "agt-x"), "cm.wibo835.agt-x")
        self.assertEqual(cm_role("wibo835", "safety"), "cm.wibo835.role.safety")


class TestAID(unittest.TestCase):
    def test_valid(self):
        aid().validate()

    def test_bad_uid(self):
        with self.assertRaises(MessageValidationError):
            aid(uid="navguy").validate()

    def test_tier_range(self):
        with self.assertRaises(MessageValidationError):
            aid(tier=5).validate()

    def test_controls_no_wildcard(self):
        with self.assertRaises(MessageValidationError):
            aid(controls=["wibo835.nav.*"]).validate()

    def test_announce_routes_as_cm_announce(self):
        bus = MembraneBus()
        got = []
        bus.subscribe("cm.announce", lambda m: got.append(m))
        a = aid()
        self.assertTrue(bus.publish(a.announce()))
        self.assertEqual(got[0].payload["content"]["aid"]["uid"], a.uid)

    def test_sign_verify(self):
        a = aid().sign_with(b"platform-ca-secret")
        self.assertTrue(verify(a.to_dict(), b"platform-ca-secret"))
        self.assertFalse(verify(a.to_dict(), b"wrong-key"))


class TestCMMessage(unittest.TestCase):
    def test_propose_requires_fallback(self):
        with self.assertRaises(MessageValidationError):
            CMMessage(msg_type=CMType.PROPOSE, sender_uid="agt-wibo835-navigation-001",
                      subject="alter_course").to_message()

    def test_propose_with_fallback_ok(self):
        m = CMMessage(msg_type=CMType.PROPOSE, sender_uid="agt-wibo835-navigation-001",
                      subject="alter_course", proposal_id="p1",
                      fallback={"action": "reduce_speed_and_alert_crew"}).to_message()
        self.assertEqual(m.sigma, "cm.propose")
        self.assertTrue(m.is_action)                 # cm.propose is action-layer (Ω₈)

    def test_inform_is_not_action_and_flows_in_dream(self):
        bus = MembraneBus()
        got = []
        bus.subscribe("cm.inform", lambda m: got.append(m))
        m = CMMessage(msg_type=CMType.INFORM, sender_uid="agt-wibo835-navigation-001",
                      subject="position", content={"value": 0.94}, mode=Mode.DREAM).to_message()
        self.assertTrue(bus.publish(m))              # info flows even in DREAM

    def test_propose_suppressed_in_dream(self):
        bus = MembraneBus()
        m = CMMessage(msg_type=CMType.PROPOSE, sender_uid="agt-wibo835-navigation-001",
                      subject="x", fallback={"a": 1}, mode=Mode.DREAM).to_message()
        self.assertFalse(bus.publish(m))             # Ω₈ suppresses action in DREAM

    def test_proposal_ttl_expiry(self):
        self.assertTrue(proposal_expired(monotonic_tau() - 1))
        self.assertFalse(proposal_expired(monotonic_tau() + 10_000_000_000))
        self.assertFalse(proposal_expired(None))


if __name__ == "__main__":
    unittest.main()

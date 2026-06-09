import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mebus import (
    MMessage, Mode, MembraneBus, monotonic_tau, effective_trust,
    MessageExpired, TrustFloorDiscarded, DreamActionSuppressed,
)


def msg(**kw):
    base = dict(sigma="cm.inform", payload={"x": 1}, destination="urbi")
    base.update(kw)
    return MMessage(**base)


class TestEffectiveTrust(unittest.TestCase):
    def test_equation(self):
        self.assertAlmostEqual(effective_trust(0.8, anomaly=0.4), 0.6)
        self.assertAlmostEqual(effective_trust(0.05, cross_validated=True), 0.15)
        self.assertEqual(effective_trust(2.0), 1.0)   # clamped

    def test_default_full_trust(self):
        self.assertEqual(msg().effective_trust(), 1.0)


class TestTrustGate(unittest.TestCase):
    def test_low_trust_discarded(self):
        bus = MembraneBus()
        got = []
        bus.subscribe("cm.inform", lambda m: got.append(m))
        delivered = bus.publish(msg(context={"trust_score": 0.05}))
        self.assertFalse(delivered)
        self.assertEqual(got, [])
        self.assertTrue(bus.audit_log[-1]["trust_blocked"])

    def test_low_trust_strict_raises(self):
        with self.assertRaises(TrustFloorDiscarded):
            MembraneBus().publish(msg(context={"trust_score": 0.0}), strict=True)

    def test_cross_validation_rescues(self):
        bus = MembraneBus()
        delivered = bus.publish(msg(context={"trust_score": 0.05, "cross_validated": True}))
        self.assertTrue(delivered)

    def test_enforce_off_delivers(self):
        bus = MembraneBus(enforce_trust=False)
        self.assertTrue(bus.publish(msg(context={"trust_score": 0.0})))


class TestFreshness(unittest.TestCase):
    def test_expired_discarded(self):
        bus = MembraneBus()
        delivered = bus.publish(msg(context={"t_expires": monotonic_tau() - 1_000}))
        self.assertFalse(delivered)
        self.assertTrue(bus.audit_log[-1]["expired"])

    def test_fresh_delivered(self):
        bus = MembraneBus()
        self.assertTrue(bus.publish(msg(context={"t_expires": monotonic_tau() + 10_000_000_000})))

    def test_expired_strict_raises(self):
        with self.assertRaises(MessageExpired):
            MembraneBus().publish(msg(context={"t_expires": monotonic_tau() - 1}), strict=True)


class TestLiminal(unittest.TestCase):
    def test_liminal_action_delivered_but_advisory(self):
        bus = MembraneBus()
        got = []
        bus.subscribe("cm.request", lambda m: got.append(m))
        delivered = bus.publish(msg(sigma="cm.request", destination="orbi", mode=Mode.LIMINAL))
        self.assertTrue(delivered)                       # delivered (unlike DREAM)
        self.assertEqual(len(got), 1)
        self.assertTrue(bus.audit_log[-1]["advisory"])   # but flagged advisory

    def test_dream_still_suppresses(self):
        with self.assertRaises(DreamActionSuppressed):
            MembraneBus().publish(msg(sigma="cm.request", destination="orbi", mode=Mode.DREAM), strict=True)


if __name__ == "__main__":
    unittest.main()

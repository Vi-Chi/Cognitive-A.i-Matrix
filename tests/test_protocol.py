import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mebus import (
    MMessage, Mode, MembraneBus, is_action_layer,
    SchemaVersionError, InvalidModeError, MessageValidationError,
    DreamActionSuppressed, PROTOCOL_VERSION,
)


def msg(**kw):
    base = dict(sigma="m.state", payload={"x": 1}, destination="urbi")
    base.update(kw)
    return MMessage(**base)


class TestMMessage(unittest.TestCase):
    def test_valid(self):
        msg().validate()

    def test_schema_version(self):
        with self.assertRaises(SchemaVersionError):
            msg(version=99).validate()

    def test_invalid_mode(self):
        with self.assertRaises(InvalidModeError):
            msg(mode="DREAM").validate()        # str, not Mode

    def test_bad_sigma(self):
        with self.assertRaises(MessageValidationError):
            msg(sigma="nodot").validate()

    def test_missing_destination(self):
        with self.assertRaises(MessageValidationError):
            msg(destination="").validate()

    def test_roundtrip(self):
        m = msg(mode=Mode.LIMINAL, context={"trust": 0.9})
        self.assertEqual(MMessage.from_dict(m.to_dict()).to_dict(), m.to_dict())

    def test_fingerprint_deterministic(self):
        m = msg(tau=123)
        self.assertEqual(m.fingerprint(), msg(tau=123).fingerprint())


class TestActionLayer(unittest.TestCase):
    def test_known_action(self):
        self.assertTrue(is_action_layer("cm.request"))
        self.assertTrue(is_action_layer("cm.delegate"))
        self.assertTrue(is_action_layer("cmd.autopilot.heading"))

    def test_non_action(self):
        self.assertFalse(is_action_layer("m.prediction_record"))
        self.assertFalse(is_action_layer("cm.inform"))


class TestOmega8(unittest.TestCase):
    """Invariant Ω₈ — action layer suppressed in DREAM."""

    def setUp(self):
        self.bus = MembraneBus()
        self.seen = []
        for s in ("cm.request", "m.prediction_record", "cm.inform"):
            self.bus.subscribe(s, lambda m: self.seen.append(m.sigma))

    def test_action_suppressed_in_dream(self):
        delivered = self.bus.publish(msg(sigma="cm.request", destination="orbi", mode=Mode.DREAM))
        self.assertFalse(delivered)
        self.assertNotIn("cm.request", self.seen)

    def test_action_suppressed_strict_raises(self):
        with self.assertRaises(DreamActionSuppressed):
            self.bus.publish(msg(sigma="cm.request", destination="orbi", mode=Mode.DREAM), strict=True)

    def test_cognition_passes_in_dream(self):
        delivered = self.bus.publish(msg(sigma="m.prediction_record", destination="urbi", mode=Mode.DREAM))
        self.assertTrue(delivered)
        self.assertIn("m.prediction_record", self.seen)

    def test_action_passes_in_wake(self):
        delivered = self.bus.publish(msg(sigma="cm.request", destination="orbi", mode=Mode.WAKE))
        self.assertTrue(delivered)
        self.assertIn("cm.request", self.seen)

    def test_audit_records_suppression(self):
        self.bus.publish(msg(sigma="cm.delegate", destination="orbi", mode=Mode.DREAM))
        self.assertTrue(self.bus.audit_log[-1]["suppressed"])


if __name__ == "__main__":
    unittest.main()

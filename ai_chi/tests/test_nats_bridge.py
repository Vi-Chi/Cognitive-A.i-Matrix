"""NATS bridge wire (de)serialization and membrane conformance.

The module imports without nats-py (optional); these tests exercise the pure wire
helpers, which is where the bug lived: μ must round-trip back to a Mode enum.
"""
import asyncio
from types import SimpleNamespace
import unittest

from ai_chi.bus import MembraneBus, Mode, MMessage
from ai_chi.bus.transports.nats_bridge import (
    DEFAULT_OUTBOUND_SIGMA_ALLOWLIST,
    NatsTransportBridge,
    from_wire,
    routing_key,
    sigma_allowed,
    to_wire,
    validate_nats_security,
)


def _msg(mode):
    return MMessage(sigma="m.belief", payload={"x": 1}, destination="urbi",
                    mode=mode, context={"trust_score": 0.9}).validate()


class WireRoundTripTests(unittest.TestCase):
    def test_mode_round_trips_to_enum(self):
        for mode in (Mode.WAKE, Mode.LIMINAL, Mode.DREAM):
            out = from_wire(to_wire(_msg(mode)))
            self.assertIsInstance(out.mode, Mode)   # <-- the bug: was a bare str
            self.assertIs(out.mode, mode)

    def test_full_envelope_preserved(self):
        m = _msg(Mode.DREAM)
        out = from_wire(to_wire(m))
        self.assertEqual(out.sigma, "m.belief")
        self.assertEqual(out.payload, {"x": 1})
        self.assertEqual(out.destination, "urbi")
        self.assertEqual(out.context["trust_score"], 0.9)
        self.assertEqual(out.fingerprint(), m.fingerprint())  # stable content hash

    def test_reconstructed_message_is_valid(self):
        # from_wire runs validate(); a bad mode would have raised InvalidModeError.
        out = from_wire(to_wire(_msg(Mode.WAKE)))
        self.assertIsNotNone(out.validate())

    def test_routing_key_uses_sigma_class(self):
        self.assertEqual(routing_key(_msg(Mode.WAKE)), "mebus.m.belief")

    def test_bytes_and_str_accepted(self):
        wire = to_wire(_msg(Mode.WAKE))
        self.assertIs(from_wire(wire).mode, Mode.WAKE)            # bytes
        self.assertIs(from_wire(wire.decode()).mode, Mode.WAKE)  # str

    def test_inbound_federation_reapplies_membrane_gates(self):
        bus = MembraneBus()
        bridge = object.__new__(NatsTransportBridge)
        bridge.node_id = "remote_node"
        bridge.inbound_trust_ceiling = 0.5
        bridge.allow_inbound_actions = True
        bridge.local_publisher = bus.publish
        action = MMessage(
            sigma="m.action",
            payload={"do": "x"},
            destination="world",
            mode=Mode.DREAM,
            context={"trust_score": 1.0, "provenance": ["remote"]},
        ).validate()

        inbound = SimpleNamespace(data=to_wire(action), subject="mebus.m.m.action")
        asyncio.run(bridge._inbound(inbound))

        self.assertFalse(bus.audit_log[-1]["delivered"])
        self.assertEqual(bus.audit_log[-1]["σ"], "m.action")

    def test_subtyped_inbound_action_is_dropped_by_default(self):
        bus = MembraneBus()
        bridge = object.__new__(NatsTransportBridge)
        bridge.node_id = "remote_node"
        bridge.inbound_trust_ceiling = 0.5
        bridge.allow_inbound_actions = False
        bridge.local_publisher = bus.publish
        action = MMessage(
            sigma="m.action.helm",
            payload={"do": "x"},
            destination="world",
            mode=Mode.WAKE,
            context={"trust_score": 1.0, "provenance": ["remote"]},
        ).validate()

        inbound = SimpleNamespace(data=to_wire(action), subject="mebus.m.action.helm")
        asyncio.run(bridge._inbound(inbound))

        self.assertEqual(bus.audit_log, [])

    def test_inbound_federation_caps_trust_and_restamps_provenance(self):
        bus = MembraneBus()
        received = []
        bus.subscribe("m.belief", received.append)
        bridge = object.__new__(NatsTransportBridge)
        bridge.node_id = "remote_node"
        bridge.inbound_trust_ceiling = 0.4
        bridge.allow_inbound_actions = False
        bridge.local_publisher = bus.publish
        msg = MMessage(
            sigma="m.belief",
            payload={"x": 1},
            destination="urbi",
            mode=Mode.WAKE,
            context={"trust_score": 1.0, "provenance": ["self-asserted"]},
        ).validate()

        inbound = SimpleNamespace(data=to_wire(msg), subject="mebus.m.belief")
        asyncio.run(bridge._inbound(inbound))

        self.assertEqual(bus.audit_log[-1]["trust"], 0.4)
        self.assertEqual(received[0].context["provenance"], ["nats:remote_node", "subject:mebus.m.belief"])
        self.assertEqual(received[0].context["federated_original_provenance"], ["self-asserted"])

    def test_outbound_allowlist_excludes_action_layer_by_default(self):
        self.assertTrue(sigma_allowed("m.prediction_record", DEFAULT_OUTBOUND_SIGMA_ALLOWLIST))
        self.assertTrue(sigma_allowed("ext.nmea", DEFAULT_OUTBOUND_SIGMA_ALLOWLIST))
        self.assertFalse(sigma_allowed("m.action", DEFAULT_OUTBOUND_SIGMA_ALLOWLIST))
        self.assertFalse(sigma_allowed("m.action.helm", DEFAULT_OUTBOUND_SIGMA_ALLOWLIST))

    def test_non_loopback_nats_requires_auth_and_tls_options(self):
        validate_nats_security("nats://127.0.0.1:4222")
        with self.assertRaises(ValueError):
            validate_nats_security("nats://192.0.2.10:4222")
        validate_nats_security(
            "nats://192.0.2.10:4222",
            {"token": "redacted-token-ref", "tls": True},
        )


if __name__ == "__main__":
    unittest.main()

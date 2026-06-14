"""SigintMapperObserver — passive RF intake; receive-only; range-gated."""
import unittest

from ai_chi.bus import MembraneBus, is_action_layer
from ai_chi.core.observe import SigintMapperObserver


class TestSigint(unittest.TestCase):
    def test_detection_emits_observation(self):
        bus = MembraneBus()
        seen = []
        bus.subscribe("ext.observation", lambda m: seen.append(m))
        obs = SigintMapperObserver(bus)
        msg = obs.ingest_detection(freq_mhz=156.8, classification="ais", dbm=-72,
                                   bearing_deg=210, range_km=12)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.sigma, "ext.observation")
        self.assertFalse(msg.is_action)
        self.assertEqual(msg.payload["extracted"]["passive"], True)
        self.assertEqual(len(seen), 1)

    def test_range_gate_drops_far_detection(self):
        obs = SigintMapperObserver(MembraneBus(), range_gate_km=100.0)
        self.assertIsNone(obs.ingest_detection(freq_mhz=400.0, range_km=250.0))

    def test_no_transmit_path_exists(self):
        # receive-only invariant: the class exposes no send/transmit method
        obs = SigintMapperObserver(MembraneBus())
        self.assertTrue(obs.TRANSMIT_PROHIBITED)
        for attr in dir(obs):
            self.assertNotIn(attr.lower(), {"transmit", "send", "tx", "broadcast"})
        self.assertFalse(is_action_layer("ext.observation"))


if __name__ == "__main__":
    unittest.main()

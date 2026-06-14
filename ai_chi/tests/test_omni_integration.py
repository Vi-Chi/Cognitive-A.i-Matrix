"""Omni → herald → PolicyGate end-to-end: a herald convened through the REAL gate."""
import tempfile
import unittest
from pathlib import Path

from ai_chi.orbi.spawner import Spawner
from ai_chi.orbi.ledger import OrbiLedger
from ai_chi.orbi.omni import OmniCenter, OmniError


def _support(_mission):
    return ("+", "audit ok")


class OmniEndToEndTests(unittest.TestCase):
    def _omni(self, tmp):
        spawner = Spawner(ledger=OrbiLedger(Path(tmp) / "ledger"), audit_fn=_support)
        return OmniCenter(spawner=spawner), spawner

    def test_convene_lumen_runs_through_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            omni, _ = self._omni(tmp)
            instance, result, decision = omni.convene("Lumen", "observe the field")
            self.assertTrue(decision.allowed)              # gate cleared (SUPPORT audit)
            self.assertEqual(instance.template, "h1.sight.v0")
            self.assertEqual(instance.status, "terminated")  # bounded ghost ran + closed
            self.assertIsNotNone(result)

    def test_convene_out_of_realm_refused_before_spawn(self):
        with tempfile.TemporaryDirectory() as tmp:
            omni, spawner = self._omni(tmp)
            with self.assertRaises(OmniError):
                omni.convene("Lumen", "dream", origin_realm="possibility")

    def test_herald_auto_registered_in_spawner(self):
        with tempfile.TemporaryDirectory() as tmp:
            omni, spawner = self._omni(tmp)
            omni.convene("Mneme", "recall lineage")
            self.assertIn("h2.memory.v0", spawner.registry)


if __name__ == "__main__":
    unittest.main()

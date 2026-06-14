from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_chi.core.cal import CalibrationMonitor
from ai_chi.core.loop import RealityLoop, message_record_id
from ai_chi.core.observe import ManualTextObserver
from ai_chi.bus import Mode


class FakeAuditor:
    def __init__(self, state: str = "=", confidence: float = 0.4, route: str = "dream_layer") -> None:
        self.state = state
        self.confidence = confidence
        self.route = route
        self.calls: list[str] = []

    def audit(self, claim: str, **_: object) -> dict:
        self.calls.append(claim)
        return {
            "state": self.state,
            "confidence": self.confidence,
            "reason": "fake-auditor",
            "route": self.route,
        }


class RealityLoopTests(unittest.TestCase):
    def test_observation_uses_canonical_mmessage(self) -> None:
        msg = ManualTextObserver().observe("The bilge pump is active")
        self.assertEqual(msg.sigma, "ext.observation")
        self.assertEqual(msg.mode, Mode.WAKE)
        self.assertIsInstance(msg.tau, int)
        self.assertIn("π", msg.to_dict())

    def test_submit_claim_routes_suspension_to_prediction_stream(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fake = FakeAuditor("=")
            loop = RealityLoop(ledger_dir=td, auditor=fake)
            obs, audit = loop.submit_claim("unresolved hardware future")

            self.assertEqual(obs.sigma, "ext.observation")
            self.assertEqual(audit.sigma, "m.prediction_record")
            self.assertTrue(fake.calls)
            self.assertTrue((Path(td) / "evidence.jsonl").exists())
            self.assertTrue((Path(td) / "predictions.jsonl").exists())
            self.assertEqual(len(tuple(loop.ledger.stream_names())), 5)

    def test_outcome_and_calibration_write_canonical_streams(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            loop = RealityLoop(ledger_dir=td, auditor=FakeAuditor("="))
            _, audit = loop.submit_claim("maybe safe")
            pred_id = message_record_id(audit)
            outcome, cal = loop.record_outcome(
                prediction_id=pred_id,
                confidence=0.4,
                actual_state="held true",
                matched=True,
            )
            self.assertEqual(outcome.sigma, "ext.outcome")
            self.assertEqual(cal.sigma, "m.calibration")
            self.assertTrue((Path(td) / "outcomes.jsonl").exists())
            self.assertTrue((Path(td) / "calibration.jsonl").exists())
            line = (Path(td) / "calibration.jsonl").read_text(encoding="utf-8").splitlines()[-1]
            self.assertEqual(json.loads(line)["σ"], "m.calibration")


class CalibrationTests(unittest.TestCase):
    def test_single_bad_sample_does_not_halt(self) -> None:
        cal = CalibrationMonitor(min_window=5)
        msg = cal.evaluate("p1", 0.95, matched=False, actual_state="false")
        self.assertEqual(msg.sigma, "m.calibration")
        self.assertFalse(msg.payload["halt"])

    def test_sustained_divergence_halts(self) -> None:
        cal = CalibrationMonitor(min_window=5, brier_halt_threshold=0.45)
        msg = None
        for i in range(5):
            msg = cal.evaluate(f"p{i}", 0.95, matched=False, actual_state="false")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.sigma, "cm.alert")
        self.assertTrue(msg.payload["halt"])
        self.assertEqual(msg.payload["epistemic_shift"], "divergent_halt")

    def test_underconfidence_is_bilateral(self) -> None:
        cal = CalibrationMonitor(min_window=3, brier_halt_threshold=1.0)
        msg = None
        for i in range(3):
            msg = cal.evaluate(f"p{i}", 0.2, matched=True, actual_state="true")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.sigma, "m.calibration")
        self.assertEqual(msg.payload["epistemic_shift"], "underconfident")


class CanonGuardTests(unittest.TestCase):
    def test_no_parallel_aicore_schema_module(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "mebus" / "schema.py"
        self.assertFalse(schema_path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)

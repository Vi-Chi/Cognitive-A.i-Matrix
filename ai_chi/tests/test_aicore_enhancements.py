"""Tests for the aicore enhancements:
  A) CAL/Ω₄ ECE + MCE + reliability bins + high-conf failure rate (additive).
  B) Audit→Memory arc — Reality Loop outcomes promote into Urbi memory.

Offline, stdlib. Helpers mk_. The fake auditor avoids touching live Ollama/Hailo.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_chi.core.cal import CalibrationMonitor
from ai_chi.core.loop import RealityLoop
from ai_chi.urbi.memory import MemoryStore, Tier


class FakeSuspend:
    def audit(self, claim: str, **_) -> dict:
        return {"state": "=", "confidence": 0.4, "reason": "smoke", "route": "dream_layer"}


# ---------------------------------------------------------------------------
class TestCalibrationECE(unittest.TestCase):
    def _feed(self, mon, pairs):
        msg = None
        for i, (conf, matched) in enumerate(pairs):
            msg = mon.evaluate(f"p{i}", conf, matched=matched)
        return msg

    def test_payload_has_new_metrics_without_dropping_old(self):
        mon = CalibrationMonitor(min_window=4)
        msg = self._feed(mon, [(0.5, True), (0.5, False), (0.5, True), (0.5, False)])
        p = msg.payload
        for k in ("ece", "mce", "reliability_bins", "high_conf_failure_rate",
                  "well_calibrated"):
            self.assertIn(k, p)
        # old keys preserved (no regression)
        for k in ("brier_score", "mean_brier_score", "epistemic_shift", "halt"):
            self.assertIn(k, p)

    def test_well_calibrated_stream(self):
        # conf 0.5 with 50% accuracy -> gap ~0 -> low ECE -> well_calibrated
        mon = CalibrationMonitor(min_window=4)
        msg = self._feed(mon, [(0.5, True), (0.5, False)] * 4)
        self.assertLess(msg.payload["ece"], 0.10)
        self.assertTrue(msg.payload["well_calibrated"])

    def test_overconfident_stream_flagged(self):
        # high confidence, always wrong -> high ECE + high-conf failures + not calibrated
        mon = CalibrationMonitor(min_window=4)
        msg = self._feed(mon, [(0.95, False)] * 6)
        self.assertGreater(msg.payload["ece"], 0.5)
        self.assertEqual(msg.payload["high_conf_failure_rate"], 1.0)
        self.assertFalse(msg.payload["well_calibrated"])
        self.assertEqual(msg.payload["epistemic_shift"], "divergent_halt")  # brier halt still works

    def test_reliability_bins_are_equal_mass(self):
        mon = CalibrationMonitor(min_window=2, cal_bins=3)
        msg = self._feed(mon, [(c / 10, c % 2 == 0) for c in range(1, 10)])
        bins = msg.payload["reliability_bins"]
        self.assertTrue(bins)
        self.assertEqual(sum(b["n"] for b in bins), len(mon.samples))


# ---------------------------------------------------------------------------
class TestAuditToMemoryArc(unittest.TestCase):
    def _loop(self, d):
        return RealityLoop(ledger_dir=str(Path(d) / "ledger"),
                           auditor=FakeSuspend(),
                           memory=MemoryStore(Path(d) / "mem"))

    def test_matched_outcome_promotes_to_core(self):
        with tempfile.TemporaryDirectory() as d:
            loop = self._loop(d)
            loop.record_outcome(prediction_id="p1", confidence=0.9,
                                actual_state="held", matched=True)
            self.assertEqual(loop.last_promotion.decision, "promoted")
            self.assertEqual(len(loop.memory.read(Tier.CORE)), 1)

    def test_wrong_outcome_preserved_in_negative(self):
        with tempfile.TemporaryDirectory() as d:
            loop = self._loop(d)
            loop.record_outcome(prediction_id="p2", confidence=0.9,
                                actual_state="failed", matched=False)
            self.assertEqual(loop.last_promotion.decision, "rejected")
            self.assertEqual(len(loop.memory.read(Tier.NEGATIVE)), 1)
            self.assertEqual(loop.memory.read(Tier.CORE), [])

    def test_no_memory_means_no_writes_and_no_break(self):
        # Default loop (no memory) behaves exactly as before.
        with tempfile.TemporaryDirectory() as d:
            loop = RealityLoop(ledger_dir=str(Path(d) / "ledger"), auditor=FakeSuspend())
            outcome, cal = loop.record_outcome(prediction_id="p3", confidence=0.7,
                                               actual_state="x", matched=True)
            self.assertIsNone(loop.memory)
            self.assertIsNone(loop.last_promotion)
            self.assertEqual(cal.sigma, "m.calibration")


if __name__ == "__main__":
    unittest.main()

"""Adversarial tests for the observe adapters, Dream ΦΔ, and CAL bus monitor.

Real assertions against the canon modules (restored 2026-06-08 after the no-op stub regression).
Run from the A.i root:
    PYTHONPATH=.:Ai_Stack/MEBUS/mebus/src:Ai_Stack/Urbi/cognitive_matrix_repo \
        python -m unittest ai_chi.tests.test_observe_dream_cal -v
"""
from __future__ import annotations

import unittest

from ai_chi.bus import MembraneBus, MMessage, Mode, is_action_layer
from ai_chi.core.observe import CM5HostObserver, MaritimeNMEAObserver
from ai_chi.core.cal import CalibrationBusMonitor, CalibrationMonitor
from ai_chi.urbi.dream import DreamConsolidator


def _capture(bus: MembraneBus, sigma: str) -> list[MMessage]:
    seen: list[MMessage] = []
    bus.subscribe(sigma, seen.append)
    return seen


class ObserveTests(unittest.TestCase):
    def test_cm5_thermal_emits_canonical_observation(self) -> None:
        bus = MembraneBus()
        seen = _capture(bus, "ext.observation")
        obs = CM5HostObserver(bus, thermal_zone="/nonexistent")  # graceful -99.0
        msg = obs.poll_once()
        self.assertEqual(msg.sigma, "ext.observation")
        self.assertFalse(is_action_layer(msg.sigma))
        self.assertEqual(msg.mode, Mode.WAKE)
        self.assertIsInstance(msg.tau, int)              # monotonic, not epoch
        self.assertEqual(msg.version, 1)                 # int, not "1.0.0"
        self.assertEqual(msg.context["trust_score"], 1.0)
        self.assertEqual(len(seen), 1)

    def test_nmea_emits_observation_with_raw_sentence(self) -> None:
        bus = MembraneBus()
        seen = _capture(bus, "ext.observation")
        MaritimeNMEAObserver(bus).ingest_nmea_sentence("$GPRMC,123519,A,4807.038,N", rx_confidence=0.8)
        self.assertEqual(seen[0].payload["raw_data"], "$GPRMC,123519,A,4807.038,N")
        self.assertEqual(seen[0].context["trust_score"], 0.8)


class DreamTests(unittest.TestCase):
    def mk_outcome(self, matched: bool) -> MMessage:
        return MMessage(sigma="ext.outcome",
                        payload={"target_prediction_id": "p1", "matched": matched, "actual_state": "x"},
                        destination="cal", context={"trust_score": 1.0, "provenance": ["t"]}).validate()

    def test_queues_only_errors_and_commits_cognition_patch(self) -> None:
        bus = MembraneBus()
        patches = _capture(bus, "m.belief")
        dc = DreamConsolidator(bus)
        bus.publish(self.mk_outcome(True))    # success — ignored
        bus.publish(self.mk_outcome(False))   # error — queued
        self.assertEqual(len(dc.error_queue), 1)
        committed = dc.run_cycle()
        self.assertEqual(committed, 1)
        self.assertEqual(dc.error_queue, [])
        self.assertEqual(patches[0].sigma, "m.belief")
        self.assertFalse(is_action_layer(patches[0].sigma))   # Urbi never acts
        self.assertEqual(patches[0].mode, Mode.DREAM)

    def test_sys_mode_dream_triggers_cycle(self) -> None:
        bus = MembraneBus()
        dc = DreamConsolidator(bus)
        bus.publish(self.mk_outcome(False))
        bus.publish(MMessage(sigma="sys.mode", payload={"mode": "DREAM"}, destination="all").validate())
        self.assertEqual(dc.error_queue, [])  # consolidated on DREAM signal


class CalBusTests(unittest.TestCase):
    def mk_outcome(self, conf, matched) -> MMessage:
        return MMessage(sigma="ext.outcome",
                        payload={"target_prediction_id": "p1", "matched": matched,
                                 "actual_state": "x", "original_confidence": conf},
                        destination="cal", context={"trust_score": 1.0, "provenance": ["t"]}).validate()

    def testmk_outcome_delegates_and_publishes_calibration(self) -> None:
        bus = MembraneBus()
        cals = _capture(bus, "m.calibration")
        CalibrationBusMonitor(bus, CalibrationMonitor(min_window=1))
        bus.publish(self.mk_outcome(0.9, True))
        self.assertEqual(cals[0].sigma, "m.calibration")
        self.assertIn("brier_score", cals[0].payload)

    def test_missing_confidence_skips_gracefully(self) -> None:
        bus = MembraneBus()
        cals = _capture(bus, "m.calibration")
        CalibrationBusMonitor(bus, CalibrationMonitor(min_window=1))
        bus.publish(MMessage(sigma="ext.outcome",
                             payload={"target_prediction_id": "p1", "matched": True},
                             destination="cal").validate())
        self.assertEqual(cals, [])  # no confidence -> no calibration emitted


if __name__ == "__main__":
    unittest.main(verbosity=2)

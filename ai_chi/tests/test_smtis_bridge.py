"""SMTIS → core PredictionRecord bridge — mapping + the action-refusal membrane."""
import unittest

from ai_chi.bus import MembraneBus, Mode, PredictionRecord, is_action_layer
from ai_chi.core.observe import (
    SmtisPredictionBridge, prediction_record_from_smtis, SmtisBridgeError, SMTIS_MODE_MAP,
)
from ai_chi.urbi.dream import DreamReplayAuditor


def smtis_rec(rid="f1", *, mode="LIVE", safe_for_action=False, conf=0.7,
              kind="route", inputs=None, **extra):
    d = {
        "id": rid, "mode": mode, "kind": kind, "summary": "advisory forecast",
        "prediction_for": "ownship", "confidence": conf, "risk_score": 0.2,
        "source_inputs": inputs if inputs is not None else ["signalk", "ais"],
        "alternatives": ["tack_port", "tack_stbd"],
        "audit": {"safe_for_display": True, "safe_for_action": safe_for_action,
                  "requires_human_confirmation": True, "stale_inputs": False,
                  "conflicting_sources": False},
    }
    d.update(extra)
    return d


class TestMapping(unittest.TestCase):
    def test_mode_map_live_sim_replay(self):
        self.assertEqual(SMTIS_MODE_MAP, {"LIVE": Mode.WAKE, "SIMULATION": Mode.LIMINAL, "REPLAY": Mode.DREAM})
        self.assertEqual(prediction_record_from_smtis(smtis_rec(mode="LIVE")).mu_at_time, Mode.WAKE)
        self.assertEqual(prediction_record_from_smtis(smtis_rec(mode="SIMULATION")).mu_at_time, Mode.LIMINAL)
        self.assertEqual(prediction_record_from_smtis(smtis_rec(mode="REPLAY")).mu_at_time, Mode.DREAM)

    def test_fields_mapped(self):
        r = prediction_record_from_smtis(smtis_rec(rid="x", inputs=["signalk", "grib"]))
        self.assertIsInstance(r, PredictionRecord)
        self.assertEqual(r.record_id, "x")
        self.assertEqual(r.causal_parents, ["signalk", "grib"])     # source feeds = causal parents
        self.assertEqual(r.domain, "smtis.route")
        self.assertEqual(r.predicted_outcome["action_admissible"], False)
        self.assertEqual(r.belief_state["prediction_for"], "ownship")

    def test_unknown_mode_refused(self):
        with self.assertRaises(SmtisBridgeError):
            prediction_record_from_smtis(smtis_rec(mode="TELEPORT"))


class TestActionMembrane(unittest.TestCase):
    def test_safe_for_action_true_is_refused(self):
        with self.assertRaises(SmtisBridgeError):
            prediction_record_from_smtis(smtis_rec(safe_for_action=True))

    def test_missing_audit_fails_closed(self):
        d = smtis_rec()
        del d["audit"]
        with self.assertRaises(SmtisBridgeError):
            prediction_record_from_smtis(d)

    def test_missing_safe_for_action_key_fails_closed(self):
        d = smtis_rec()
        d["audit"].pop("safe_for_action")
        with self.assertRaises(SmtisBridgeError):
            prediction_record_from_smtis(d)


class TestBridgePublish(unittest.TestCase):
    def test_ingest_publishes_cognition_not_action(self):
        seen = []
        bus = MembraneBus()
        bus.subscribe("m.prediction_record", lambda m: seen.append(m))
        msg = SmtisPredictionBridge(bus).ingest(smtis_rec(mode="LIVE"))
        self.assertEqual(msg.sigma, "m.prediction_record")
        self.assertFalse(msg.is_action)
        self.assertFalse(is_action_layer("m.prediction_record"))
        self.assertEqual(len(seen), 1)

    def test_ingest_many_skips_refused(self):
        bridge = SmtisPredictionBridge()
        recs = bridge.ingest_many([
            smtis_rec(rid="ok1", mode="REPLAY"),
            smtis_rec(rid="bad", mode="REPLAY", safe_for_action=True),  # refused
            smtis_rec(rid="ok2", mode="REPLAY"),
        ])
        self.assertEqual([r.record_id for r in recs], ["ok1", "ok2"])


class TestEndToEndReplayToDream(unittest.TestCase):
    def test_smtis_replay_feeds_a_dream_cycle(self):
        # A REPLAY session of SMTIS forecasts, some with outcomes, flows into the Dream auditor.
        bridge = SmtisPredictionBridge()
        payloads = [
            smtis_rec(rid="r1", mode="REPLAY", conf=0.9,
                      actual_outcome={"evidence": 1}, prediction_error=0.05),
            smtis_rec(rid="r2", mode="REPLAY", conf=0.95,
                      actual_outcome={"x": 1}, prediction_error=0.8),   # high-conf-wrong
        ]
        records = bridge.ingest_many(payloads)
        report = DreamReplayAuditor().run_cycle(records)
        self.assertEqual(report.processed_records, 2)
        # the high-confidence-wrong forecast surfaces as a contradiction
        self.assertTrue(any(c.kind.value == "prediction_error" for c in report.contradictions))


if __name__ == "__main__":
    unittest.main()

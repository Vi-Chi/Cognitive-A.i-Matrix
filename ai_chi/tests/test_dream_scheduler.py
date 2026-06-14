"""DreamScheduler — standing consolidation: buffer + triggers (signal/threshold/manual)."""
import unittest

from ai_chi.bus import MembraneBus, MMessage, Mode, PredictionRecord
from ai_chi.urbi.dream import DreamScheduler


def pr(rid, **kw):
    base = dict(record_id=rid, belief_state={"k": 1}, predicted_outcome={"claim": 1},
                domain="nav", confidence=0.9, causal_parents=["p1", "p2"],
                actual_outcome={"evidence": 1})
    base.update(kw)
    return PredictionRecord(**base)


class TestScheduler(unittest.TestCase):
    def test_manual_tick_runs_and_clears(self):
        s = DreamScheduler()
        s.submit(pr("a")); s.submit(pr("b"))
        self.assertEqual(s.buffered, 2)
        rep = s.tick()
        self.assertEqual(rep.processed_records, 2)
        self.assertEqual(s.buffered, 0)

    def test_empty_tick_is_none(self):
        self.assertIsNone(DreamScheduler().tick())

    def test_threshold_auto_runs(self):
        s = DreamScheduler(threshold=2)
        self.assertIsNone(s.submit(pr("a")))
        rep = s.submit(pr("b"))           # hits threshold → auto cycle
        self.assertIsNotNone(rep)
        self.assertEqual(s.buffered, 0)

    def test_bus_record_buffers_then_dream_signal_triggers(self):
        bus = MembraneBus()
        emitted = []
        bus.subscribe("m.urbi.dream", lambda m: emitted.append(m))
        s = DreamScheduler(bus)
        bus.publish(pr("a").to_message(mode=Mode.WAKE))   # m.prediction_record → buffered
        bus.publish(pr("b").to_message(mode=Mode.WAKE))
        self.assertEqual(s.buffered, 2)
        bus.publish(MMessage(sigma="sys.mode", payload={"mode": "DREAM"},
                             destination="all").validate())
        self.assertEqual(s.buffered, 0)                   # cycle ran
        self.assertEqual(len(emitted), 1)                 # report emitted as cognition
        self.assertEqual(emitted[0].sigma, "m.urbi.dream")
        self.assertFalse(emitted[0].is_action)


if __name__ == "__main__":
    unittest.main()

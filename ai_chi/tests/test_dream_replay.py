"""DREAM Replay Auditor (ΦΔ) — tests pinning the consolidation cycle + Triad invariants."""
import unittest

from ai_chi.bus import PredictionRecord, Mode, is_action_layer
from ai_chi.urbi.dream import (
    DreamReplayAuditor, DreamReplayEngine, ContradictionEngine, ConsolidationEngine,
    ConsolidationAction, ContradictionKind, SIGMA_DREAM,
)
from ai_chi.urbi.memory import Tier


def rec(rid, *, belief=None, pred=None, actual=None, err=None, conf=0.5, domain="d",
        prov=None, tau=0):
    return PredictionRecord(
        record_id=rid, belief_state=belief or {"k": 1}, predicted_outcome=pred or {"v": 1},
        domain=domain, actual_outcome=actual, prediction_error=err, confidence=conf,
        causal_parents=prov or [], tau_start=tau,
    )


class TestReplayEngine(unittest.TestCase):
    def test_timeline_is_causally_ordered(self):
        recs = [rec("c", tau=3), rec("a", tau=1), rec("b", tau=2)]
        ids = [r.record_id for r in DreamReplayEngine().load(recs).replay_timeline()]
        self.assertEqual(ids, ["a", "b", "c"])

    def test_priority_targets_are_high_conf_wrong(self):
        recs = [rec("ok", err=0.05, conf=0.9), rec("hcw", err=0.8, conf=0.95)]
        tgt = [r.record_id for r in DreamReplayEngine().load(recs).priority_targets()]
        self.assertEqual(tgt, ["hcw"])


class TestContradictionEngine(unittest.TestCase):
    def test_detects_high_confidence_wrong(self):
        cs = ContradictionEngine().detect([rec("b", err=0.8, conf=0.95)])
        self.assertTrue(any(c.kind is ContradictionKind.PREDICTION_ERROR for c in cs))

    def test_simulacrum_echo_chamber(self):
        recs = [rec(f"s{i}", pred={"same": 1}, domain="echo", tau=i) for i in range(3)]
        cs = ContradictionEngine(simulacrum_threshold=3).detect(recs)
        self.assertTrue(any(c.kind is ContradictionKind.SIMULACRUM for c in cs))

    def test_no_simulacrum_below_threshold(self):
        recs = [rec(f"s{i}", pred={"same": 1}, domain="echo", tau=i) for i in range(2)]
        cs = ContradictionEngine(simulacrum_threshold=3).detect(recs)
        self.assertFalse(any(c.kind is ContradictionKind.SIMULACRUM for c in cs))

    def test_belief_conflict(self):
        recs = [
            rec("a", belief={"pos": 1}, actual={"x": 1}, domain="nav", tau=1),
            rec("b", belief={"pos": 1}, actual={"x": 9}, domain="nav", tau=2),
        ]
        cs = ContradictionEngine().detect(recs)
        self.assertTrue(any(c.kind is ContradictionKind.BELIEF_CONFLICT for c in cs))


class TestConsolidation(unittest.TestCase):
    def test_cross_supported_promotes_but_never_to_core(self):
        # strong: high kappa + 2 provenance + claim&evidence -> [+]
        r = rec("p", conf=0.9, prov=["p1", "p2"], pred={"claim": 1}, actual={"evidence": 1})
        prop = ConsolidationEngine().propose_one(r)
        self.assertEqual(prop.action, ConsolidationAction.PROMOTE)
        self.assertEqual(prop.target_tier, Tier.SEMANTIC)
        self.assertNotEqual(prop.target_tier, Tier.CORE)

    def test_contradiction_quarantines(self):
        # urbi writing world state = constitutional violation -> contradiction -> quarantine
        r = rec("v", conf=0.9, prov=["p1", "p2"])
        r.predicted_outcome = {"writes_world_state": True, "source": "urbi"}
        prop = ConsolidationEngine().propose_one(r)
        self.assertEqual(prop.action, ConsolidationAction.QUARANTINE)
        self.assertEqual(prop.target_tier, Tier.QUARANTINE)

    def test_divergent_outlier_preserved_not_dropped(self):
        # [=] with high error -> PRESERVE_OUTLIER (Axiom 11)
        r = rec("o", conf=0.3, err=0.6, prov=["p1"])
        prop = ConsolidationEngine().propose_one(r)
        self.assertEqual(prop.action, ConsolidationAction.PRESERVE_OUTLIER)

    def test_no_proposal_targets_core(self):
        recs = [
            rec("p", conf=0.9, prov=["p1", "p2"], pred={"claim": 1}, actual={"evidence": 1}),
            rec("o", conf=0.3, err=0.6),
        ]
        for prop in ConsolidationEngine().propose(recs):
            self.assertNotEqual(prop.target_tier, Tier.CORE)


class TestDreamCycleInvariants(unittest.TestCase):
    def test_emitted_message_is_cognition_not_action(self):
        a = DreamReplayAuditor()
        report = a.run_cycle([rec("a", conf=0.9, prov=["p1", "p2"])])
        msg = a.to_message(report)
        self.assertEqual(msg.sigma, SIGMA_DREAM)
        self.assertFalse(msg.is_action)
        self.assertFalse(is_action_layer(SIGMA_DREAM))
        self.assertEqual(msg.mode, Mode.DREAM)
        self.assertFalse(report.to_payload()["action_allowed"])

    def test_repair_raises_coherence(self):
        # one clean record + one constitutional violation; sealing the violation lifts coherence
        clean = rec("ok", conf=0.9, prov=["p1", "p2"], pred={"claim": 1}, actual={"evidence": 1})
        bad = rec("bad", conf=0.9, prov=["p1", "p2"])
        bad.predicted_outcome = {"writes_world_state": True, "source": "urbi"}
        report = DreamReplayAuditor().run_cycle([clean, bad])
        self.assertGreaterEqual(report.coherence_after, report.coherence_before)
        self.assertGreater(report.coherence_gain, 0.0)

    def test_empty_cycle_is_safe(self):
        report = DreamReplayAuditor().run_cycle([])
        self.assertEqual(report.processed_records, 0)
        self.assertTrue(report.exit_ready)  # nothing incoherent

    def test_exit_ready_reflects_threshold(self):
        a = DreamReplayAuditor(exit_threshold=2.0)  # impossible threshold
        report = a.run_cycle([rec("a", conf=0.9, prov=["p1", "p2"])])
        self.assertFalse(report.exit_ready)

    def test_lens_can_add_but_not_grant_action(self):
        from ai_chi.urbi.dream.records import Contradiction, ContradictionKind

        class NoisyLens:
            def propose(self, records):
                return [Contradiction(claim_id="x", kind=ContradictionKind.UNRESOLVED,
                                      severity="low", detail="lens hint")]
        a = DreamReplayAuditor(lens=NoisyLens())
        report = a.run_cycle([rec("a", conf=0.9, prov=["p1", "p2"])])
        self.assertTrue(any(c.detail == "lens hint" for c in report.contradictions))
        # lens cannot make the cycle emit an action
        self.assertFalse(a.to_message(report).is_action)


if __name__ == "__main__":
    unittest.main()

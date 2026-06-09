import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mebus import (
    MembraneBus, Mode, MessageValidationError,
    DomainTag, UncertaintyType, UncertaintyDist, CausalRef, CognitionPayload,
    PredictionRecord,
)


def payload(**kw):
    base = dict(v=[], sigma=UncertaintyDist.point(42.0),
                delta=DomainTag.MARITIME_NAV, kappa=0.92)
    base.update(kw)
    return CognitionPayload(**base)


class TestDomainAndUncertainty(unittest.TestCase):
    def test_domain_values_match_adapter_strings(self):
        self.assertEqual(DomainTag.MARITIME_NAV.value, "maritime.nav")

    def test_uncertainty_constructors(self):
        self.assertEqual(UncertaintyDist.point(1).type, UncertaintyType.POINT)
        g = UncertaintyDist.gaussian(0.0, 1.0)
        self.assertEqual(g.params, {"mean": 0.0, "var": 1.0})

    def test_causal_ref(self):
        r = CausalRef(node_id="n1", timestamp=10, agent="nav")
        self.assertEqual(r.to_dict()["node_id"], "n1")


class TestCognitionPayload(unittest.TestCase):
    def test_to_message_routes_as_m_state(self):
        bus = MembraneBus()
        got = []
        bus.subscribe("m.state", lambda m: got.append(m))
        m = payload(pi=[CausalRef("gps0", 1, "nav")]).to_message()
        self.assertTrue(bus.publish(m))
        self.assertEqual(m.sigma, "m.state")
        self.assertEqual(m.context["domain"], "maritime.nav")
        self.assertEqual(m.context["provenance"], ["gps0"])
        self.assertEqual(got[0].payload["delta"], "maritime.nav")

    def test_belief_passes_in_dream(self):
        # m.* cognition is not action layer → flows even in DREAM (Ω₈ only gates action)
        bus = MembraneBus()
        got = []
        bus.subscribe("m.belief", lambda m: got.append(m))
        m = payload(mu=Mode.DREAM).to_message(sigma="m.belief")
        self.assertTrue(bus.publish(m))

    def test_kappa_bounds(self):
        with self.assertRaises(MessageValidationError):
            payload(kappa=1.5).to_message()

    def test_vdim_mismatch(self):
        with self.assertRaises(MessageValidationError):
            CognitionPayload(v=[0.1, 0.2], sigma=UncertaintyDist.point(1),
                             delta=DomainTag.MARITIME_NAV, kappa=0.5, v_dim=2048).validate()


class TestRichPredictionRecord(unittest.TestCase):
    def test_high_confidence_wrong(self):
        pr = PredictionRecord(record_id="r", belief_state={}, predicted_outcome={},
                              domain="maritime.nav", confidence=0.9, prediction_error=0.4)
        self.assertTrue(pr.is_high_confidence_wrong())
        self.assertEqual(pr.classify_error(), "high_conf_wrong")

    def test_new_fields_roundtrip_in_payload(self):
        pr = PredictionRecord(record_id="r", belief_state={}, predicted_outcome={},
                              domain="maritime.nav", reversal_candidate=True, tau_start=5)
        p = pr.to_payload()
        self.assertTrue(p["reversal_candidate"])
        self.assertEqual(p["tau_start"], 5)
        self.assertEqual(p["mu_at_time"], "WAKE")


if __name__ == "__main__":
    unittest.main()

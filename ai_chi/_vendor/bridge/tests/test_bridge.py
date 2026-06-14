"""Adversarial tests for the Urbi <-> MΣBUS bridge.

Run (no Ollama needed — auditor is faked):
    cd cognitive_matrix_repo
    PYTHONPATH=.:../../MEBUS/mebus/src python -m unittest bridge.tests.test_bridge -v
"""
from __future__ import annotations

import os
import pathlib
import sys
import unittest

# --- import bootstrap: make `bridge` (repo root) and `mebus` (sibling) importable ---
_ROOT = pathlib.Path(__file__).resolve().parents[2]          # cognitive_matrix_repo
sys.path.insert(0, str(_ROOT))
try:
    import mebus  # noqa: F401
except ModuleNotFoundError:
    _cands = [os.environ.get("URBI_MEBUS_SRC", "")]
    _cands.append(str(_ROOT.parents[1] / "MEBUS" / "mebus" / "src"))  # Ai_Stack/MEBUS/mebus/src
    for _c in _cands:
        if _c and (pathlib.Path(_c) / "mebus").is_dir():
            sys.path.insert(0, _c)
            break

from mebus import MembraneBus, MMessage, Mode, is_action_layer  # noqa: E402
import bridge as B  # noqa: E402


def mk(state: str, conf: float, route: str, reason: str = "trace") -> dict:
    return {"state": state, "confidence": conf, "reason": reason, "route": route}


class FakeAuditor:
    """Returns a canned 3-6-9 verdict; records the claims it saw."""
    def __init__(self, verdict: dict) -> None:
        self.verdict = verdict
        self.calls: list[str] = []

    def audit(self, claim: str, **kw) -> dict:
        self.calls.append(claim)
        return dict(self.verdict)


class BridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = MembraneBus()
        self.seen: list[MMessage] = []
        self.bus.subscribe("m.belief", self.seen.append)
        self.bus.subscribe("m.prediction_record", self.seen.append)

    def test_confirmed_emits_belief(self) -> None:
        br = B.UrbiMebusBridge(self.bus, FakeAuditor(mk("+", 0.92, "surface")))
        out = br.audit_and_publish("depth is 4.2 m")
        self.assertTrue(out["delivered"])
        self.assertEqual(out["message"].sigma, "m.belief")
        self.assertEqual(out["message"].payload["state"], "+")
        self.assertAlmostEqual(out["message"].payload["confidence"], 0.92)

    def test_rejected_emits_belief_minus(self) -> None:
        br = B.UrbiMebusBridge(self.bus, FakeAuditor(mk("-", 0.88, "reject")))
        out = br.audit_and_publish("the sky is a fish")
        self.assertEqual(out["message"].sigma, "m.belief")
        self.assertEqual(out["message"].payload["state"], "-")
        self.assertTrue(out["delivered"])

    def test_suspended_emits_prediction_record(self) -> None:
        br = B.UrbiMebusBridge(self.bus, FakeAuditor(mk("=", 0.5, "dream_layer")))
        out = br.audit_and_publish("genuinely unresolved claim")
        self.assertEqual(out["message"].sigma, "m.prediction_record")
        self.assertTrue(out["delivered"])

    def test_cognition_flows_in_dream(self) -> None:
        # Ω₈: cognition (m.*) is NOT gated in DREAM; only action-class is.
        br = B.UrbiMebusBridge(self.bus, FakeAuditor(mk("+", 0.9, "surface")), mode=Mode.DREAM)
        out = br.audit_and_publish("a claim during dream")
        self.assertTrue(out["delivered"])
        self.assertEqual(out["message"].mode, Mode.DREAM)

    def test_urbi_never_emits_action(self) -> None:
        for st, rt in (("+", "surface"), ("-", "reject"), ("=", "dream_layer")):
            br = B.UrbiMebusBridge(self.bus, FakeAuditor(mk(st, 0.7, rt)))
            msg = br.audit_and_publish("c")["message"]
            self.assertFalse(is_action_layer(msg.sigma), f"{st} produced action σ")

    def test_inv_rejects_action_message(self) -> None:
        bad = MMessage(sigma="m.action", payload={"x": 1}, destination="orbi",
                       context={"provenance": ["urbi"]})
        with self.assertRaises(B.InvViolation):
            B.gate_emit(bad)

    def test_inv_requires_provenance(self) -> None:
        bad = MMessage(sigma="m.belief", payload={"state": "+", "confidence": 0.9},
                       destination="orbi")
        with self.assertRaises(B.InvViolation):
            B.gate_emit(bad)

    def test_inv_rejects_unstructured_belief(self) -> None:
        bad = MMessage(sigma="m.belief", payload={"text": "I think so"}, destination="orbi",
                       context={"provenance": ["urbi"]})
        with self.assertRaises(B.InvViolation):
            B.gate_emit(bad)

    def test_mode_propagation(self) -> None:
        br = B.UrbiMebusBridge(self.bus, FakeAuditor(mk("+", 0.9, "surface")))
        br.set_mode(Mode.LIMINAL)
        self.assertEqual(br.audit_and_publish("x")["message"].mode, Mode.LIMINAL)

    def test_request_round_trip(self) -> None:
        fake = FakeAuditor(mk("+", 0.9, "surface"))
        br = B.UrbiMebusBridge(self.bus, fake)
        br.subscribe_requests("m.audit_request")
        self.bus.publish(MMessage(sigma="m.audit_request",
                                  payload={"claim": "is it foggy"}, destination="urbi"))
        self.assertIn("is it foggy", fake.calls)
        self.assertTrue(any(m.sigma == "m.belief" for m in self.seen))


if __name__ == "__main__":
    unittest.main(verbosity=2)

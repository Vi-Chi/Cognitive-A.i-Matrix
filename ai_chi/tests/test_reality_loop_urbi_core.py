"""RealityLoop + UrbiAuditor: the live observe->audit path emits a proof signal.

The loop's Urbi *bridge* needs a (fake) auditor (the external `audit` module isn't
vendored); the new deterministic Urbi *Core* (UrbiAuditor) is what's under test.
"""
import tempfile
import unittest
from pathlib import Path

from ai_chi.core.loop import RealityLoop
from ai_chi.urbi import UrbiAuditor, UrbiAuditSignal, SIGMA_AUDIT


class FakeAuditor:
    """Minimal bridge auditor (mirrors test_reality_loop.FakeAuditor)."""
    def audit(self, claim: str, **_: object) -> dict:
        return {"state": "=", "confidence": 0.4, "reason": "fake", "route": "dream_layer"}


class RealityLoopUrbiCoreTests(unittest.TestCase):
    def test_default_loop_emits_no_proof_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            loop = RealityLoop(ledger_dir=Path(tmp) / "led", auditor=FakeAuditor())
            loop.submit_claim("a small vessel may be front-left")
            self.assertIsNone(loop.last_signal)   # backward-compatible: off by default

    def test_loop_with_urbi_core_emits_proof_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            loop = RealityLoop(ledger_dir=Path(tmp) / "led", auditor=FakeAuditor(),
                               urbi_core=UrbiAuditor())
            heard = []
            loop.bus.subscribe(SIGMA_AUDIT, lambda m: heard.append(m))
            loop.submit_claim("a small vessel may be front-left")
            self.assertIsInstance(loop.last_signal, UrbiAuditSignal)
            self.assertFalse(loop.last_signal.action_allowed)
            self.assertIn(loop.last_signal.epistemic_state, ("[+]", "[-]", "[=]"))
            self.assertEqual(len(heard), 1)
            self.assertEqual(heard[0].sigma, SIGMA_AUDIT)
            self.assertFalse(heard[0].is_action)   # audit is cognition, not action

    def test_audit_input_carries_claim_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            loop = RealityLoop(ledger_dir=Path(tmp) / "led", auditor=FakeAuditor(),
                               urbi_core=UrbiAuditor())
            loop.submit_claim("x", provenance="urn:test:src")
            self.assertTrue(loop.last_signal.claim_id)


if __name__ == "__main__":
    unittest.main()

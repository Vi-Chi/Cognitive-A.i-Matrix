"""The original Urbi bridge path runs SELF-CONTAINED (vendored audit.py, Ollama-offline).

Proves `import audit` resolves from ai_chi/_vendor and the real TriStateAuditor degrades
gracefully when no LLM is up — so RealityLoop works with no FakeAuditor.
"""
import tempfile
import unittest
from pathlib import Path

from ai_chi._paths import ensure_dependency_paths
ensure_dependency_paths()
import audit  # noqa: E402  (resolves from ai_chi/_vendor)

from ai_chi.core.loop import RealityLoop  # noqa: E402


class UrbiBridgeOfflineTests(unittest.TestCase):
    def test_real_bridge_audit_self_contained_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            # redirect audit.py's write paths so the package isn't polluted
            audit.CONTEXT_STORE_PATH = Path(tmp) / "ctx.json"
            audit.DREAM_LOG_PATH = Path(tmp) / "dream.log"
            loop = RealityLoop(ledger_dir=Path(tmp) / "led")   # NO fake auditor
            obs, aud = loop.submit_claim("a small vessel may be front-left")
            # the bridge emitted a cognition verdict (belief or prediction_record)
            self.assertIn(aud.sigma, ("m.belief", "m.prediction_record"))
            self.assertFalse(aud.is_action)          # Urbi audit never acts
            self.assertTrue(obs.sigma.startswith("ext."))

    def test_offline_auditor_returns_valid_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit.CONTEXT_STORE_PATH = Path(tmp) / "ctx.json"
            a = audit.TriStateAuditor()
            self.assertFalse(a.llm_up)               # offline
            v = a.audit("the bilge pump cycled twice")
            self.assertIn(v["state"], ("+", "-", "="))
            self.assertIn("confidence", v)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_trinity_secret_refs.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_trinity_secret_refs", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TrinitySecretReferenceCheckerTests(unittest.TestCase):
    def setUp(self):
        self.checker = load_checker()

    def test_presence_mode_does_not_include_secret_value(self):
        secret = "sk-" + ("a" * 32)
        rows = self.checker.build_reference_rows({"OPENAI_API_KEY": secret}, fingerprint_env=False)
        rendered = self.checker.render_text(rows, [])

        self.assertIn("OpenAI / Codex", rendered)
        self.assertIn("status=present", rendered)
        self.assertIn("fingerprint=not_requested", rendered)
        self.assertNotIn(secret, rendered)

    def test_fingerprint_mode_redacts_secret_value(self):
        secret = "sk-" + ("b" * 32)
        rows = self.checker.build_reference_rows({"OPENAI_API_KEY": secret}, fingerprint_env=True)
        encoded = json.dumps([row.to_dict() for row in rows])

        self.assertIn("sha256:", encoded)
        self.assertNotIn(secret, encoded)
        self.assertNotIn(secret[:8], encoded)
        self.assertNotIn(secret[-4:], encoded)

    def test_scanner_detects_raw_secret_patterns(self):
        secret = "sk-" + ("c" * 32)
        labels = self.checker.scan_text_for_raw_secrets("value=" + secret)

        self.assertIn("openai_key", labels)

    def test_scanner_allows_env_reference_names(self):
        labels = self.checker.scan_text_for_raw_secrets("Use ENV:OPENAI_API_KEY, not the raw value.")

        self.assertEqual(labels, [])


if __name__ == "__main__":
    unittest.main()

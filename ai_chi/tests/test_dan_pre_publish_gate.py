from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "dan_pre_publish_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("dan_pre_publish_gate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DanPrePublishGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = load_gate()
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def write(self, rel_path: str, text: str) -> Path:
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def labels(self, rel_path: str, text: str) -> list[str]:
        self.write(rel_path, text)
        return [label for hit in self.gate.scan_repo(self.root) for label in hit.labels]

    def test_bare_secret_words_do_not_block(self):
        labels = self.labels(
            "notes.md",
            "This policy discusses token budgets, password hygiene, and secret handling.\n",
        )

        self.assertEqual(labels, [])

    def test_secret_shape_blocks_without_rendering_value(self):
        secret = "sk-" + ("a" * 32)
        self.write("config.txt", f"api_key = {secret}\n")

        hits = self.gate.scan_repo(self.root)
        rendered = "\n".join(hit.render() for hit in hits)

        self.assertEqual(len(hits), 1)
        self.assertIn("secret_shape", hits[0].labels)
        self.assertNotIn(secret, rendered)

    def test_public_pii_assignment_blocks(self):
        labels = self.labels("release_notes.md", ("mar" + "ina") + ": private dock\n")

        self.assertIn("public_pii:marina", labels)

    def test_public_pii_policy_examples_without_values_do_not_block(self):
        labels = self.labels(
            "policy.md",
            "Never publish marina, berth, home address, or private link details.\n",
        )

        self.assertEqual(labels, [])

    def test_ignored_paths_and_examples_do_not_block(self):
        secret = "sk-" + ("b" * 32)
        self.write("_backup/leak.txt", secret)
        self.write(".env.example", f"OPENAI_API_KEY={secret}\n")
        self.write("_MODEL_TRINITY/bridge/inbox/codex/poke.json", f"token={secret}\n")

        self.assertEqual(self.gate.scan_repo(self.root), [])


if __name__ == "__main__":
    unittest.main()

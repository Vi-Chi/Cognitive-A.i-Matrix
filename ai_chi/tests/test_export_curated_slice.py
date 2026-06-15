from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "export_curated_slice.py"


def load_exporter():
    spec = importlib.util.spec_from_file_location("export_curated_slice", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ExportCuratedSliceTests(unittest.TestCase):
    def setUp(self):
        self.exporter = load_exporter()
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def write(self, rel_path: str, text: str = "x") -> Path:
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_bridge_runtime_queues_are_not_exported(self):
        self.write("ai_chi/__init__.py", "")
        self.write("scripts/tool.py", "print('ok')\n")
        self.write("docs/README.md", "# Docs\n")
        self.write("DO_ANYTHING_NOW.md", "# Kernel\n")
        self.write("_PROJECT_KNOWLEDGE_BASE/README.md", "# KB\n")
        self.write("_MODEL_TRINITY/README.md", "# Trinity\n")
        self.write("_MODEL_TRINITY/bridge/README.md", "# Bridge docs\n")
        self.write("_MODEL_TRINITY/bridge/trinity-bridge.config.json", "{}\n")
        self.write("_MODEL_TRINITY/bridge/inbox/codex/packet.json", "token=sk-" + ("a" * 32))
        self.write("_MODEL_TRINITY/bridge/processed/codex/packet.json", "token=sk-" + ("b" * 32))
        self.write("_MODEL_TRINITY/bridge/state/latest.json", "{}\n")

        export_dir = self.exporter.export_curated_slice(self.root)

        self.assertTrue((export_dir / "_MODEL_TRINITY" / "bridge" / "README.md").exists())
        self.assertTrue((export_dir / "_MODEL_TRINITY" / "bridge" / "trinity-bridge.config.json").exists())
        self.assertFalse((export_dir / "_MODEL_TRINITY" / "bridge" / "inbox").exists())
        self.assertFalse((export_dir / "_MODEL_TRINITY" / "bridge" / "processed").exists())
        self.assertFalse((export_dir / "_MODEL_TRINITY" / "bridge" / "state").exists())

    def test_existing_export_metadata_is_preserved(self):
        self.write("ai_chi/__init__.py", "")
        self.write("scripts/tool.py", "print('ok')\n")
        self.write("docs/README.md", "# Docs\n")
        self.write("DO_ANYTHING_NOW.md", "# Kernel\n")
        self.write("_PROJECT_KNOWLEDGE_BASE/README.md", "# KB\n")
        self.write("_MODEL_TRINITY/README.md", "# Trinity\n")
        self.write("_export/publishable_slice/.git/config", "[core]\n")
        self.write("_export/publishable_slice/_MODEL_TRINITY/bridge/inbox/old.json", "token=sk-" + ("c" * 32))

        export_dir = self.exporter.export_curated_slice(self.root)

        self.assertTrue((export_dir / ".git" / "config").exists())
        self.assertFalse((export_dir / "_MODEL_TRINITY" / "bridge" / "inbox").exists())


if __name__ == "__main__":
    unittest.main()

import unittest
import json
from pathlib import Path
import tempfile
import shutil
import sys

# Ensure scripts directory is in path
test_dir = Path(__file__).parent.resolve()
ai_chi_dir = test_dir.parent
repo_root = ai_chi_dir.parent
scripts_dir = repo_root / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

import trinity_synthesis_engine


class TestSynthesisEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.import_dir = self.temp_dir / "_backup" / "_import"
        self.import_dir.mkdir(parents=True)
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_find_raw_files_ignores_conjectures(self):
        (self.import_dir / "raw_notes.md").write_text("Hello")
        (self.import_dir / "game_system_CONJECTURE.md").write_text("Ignore me")
        (self.import_dir / "SYNTHESIS_report.md").write_text("Ignore me")
        
        files = trinity_synthesis_engine.find_raw_files(self.temp_dir)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "raw_notes.md")

    def test_build_synthesis_packet(self):
        (self.import_dir / "raw_history.txt").write_text("The Roman empire fell...")
        (self.import_dir / "raw_cyberpunk.md").write_text("Neuromancer concepts...")
        
        packet = trinity_synthesis_engine.build_synthesis_packet(self.temp_dir, batch_size=2, targets="codex")
        
        self.assertEqual(packet["kind"], "synthesis_conjecture")
        self.assertEqual(packet["to"], "codex")
        self.assertIn("Status: Conjecture", packet["body"])
        self.assertIn("Neuromancer concepts", packet["body"])
        self.assertIn("Roman empire fell", packet["body"])
        
        self.assertEqual(len(packet["files_in_scope"]), 3)

    def test_build_packet_fails_on_empty(self):
        with self.assertRaises(ValueError):
            trinity_synthesis_engine.build_synthesis_packet(self.temp_dir, batch_size=1, targets="codex")

if __name__ == "__main__":
    unittest.main()

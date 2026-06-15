import contextlib
import importlib.util
import io
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.append(str(SCRIPTS))


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class GraveyardRedactionTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.backup = self.root / "backup"
        self.backup.mkdir()
        self.db = self.root / "graveyard.db"
        self.reader = load_script("graveyard_reader")
        self.search = load_script("graveyard_search")
        self.indexer = load_script("backup_indexer")

    def db_rows(self):
        conn = sqlite3.connect(self.db)
        try:
            return conn.execute("SELECT path, content FROM documents").fetchall()
        finally:
            conn.close()

    def test_reader_redacts_before_sqlite_indexing(self):
        secret = "sk-" + ("a" * 24)
        (self.backup / "notes.md").write_text(f"# Safe\n\ncanary {secret}\n", encoding="utf-8")

        with contextlib.redirect_stdout(io.StringIO()):
            self.reader.build_index(self.backup, self.db, reset=True)

        rows = self.db_rows()
        encoded = repr(rows)
        self.assertNotIn(secret, encoded)
        self.assertIn("<REDACTED_SECRET>", rows[0][1])

    def test_reader_skips_likely_credential_paths_without_indexing(self):
        secret = "sk-" + ("b" * 24)
        (self.backup / "vapid-keys.json.txt").write_text(secret, encoding="utf-8")

        with contextlib.redirect_stdout(io.StringIO()):
            report = self.reader.build_index(self.backup, self.db, reset=True)

        self.assertEqual(report["skipped_sensitive"], 1)
        self.assertEqual(self.db_rows(), [])

    def test_search_redacts_toxic_existing_snippets(self):
        secret = "sk-" + ("c" * 24)
        conn = sqlite3.connect(self.db)
        try:
            conn.execute("CREATE VIRTUAL TABLE documents USING fts5(path, content)")
            conn.execute("INSERT INTO documents (path, content) VALUES (?, ?)", ("toxic.md", f"canary {secret}"))
            conn.commit()
        finally:
            conn.close()

        stream = io.StringIO()
        self.search.search("canary", db_path=self.db, stream=stream)

        output = stream.getvalue()
        self.assertNotIn(secret, output)
        self.assertIn("<REDACTED_SECRET>", output)

    def test_backup_indexer_redacts_summary_text(self):
        secret = "sk-" + ("d" * 24)
        path = self.backup / "summary.md"
        path.write_text(f"# Heading\n\nplain summary {secret}\n", encoding="utf-8")

        headings, summary = self.indexer.extract_headings_and_summary(path)

        self.assertEqual(headings, ["# Heading"])
        self.assertNotIn(secret, summary)
        self.assertIn("<REDACTED_SECRET>", summary)

    def test_assignment_detector_ignores_short_synthetic_construction(self):
        redaction = load_script("graveyard_redaction")

        self.assertFalse(redaction.contains_secret_shape('secret = "sk-" + ("a" * 32)'))
        self.assertFalse(redaction.contains_secret_shape("password: required"))
        self.assertFalse(redaction.contains_secret_shape("token={raw_value}"))
        self.assertFalse(redaction.contains_secret_shape('TOKEN = os.getenv("DISCORD_BOT_TOKEN")'))
        self.assertFalse(redaction.contains_secret_shape('TOKEN = env.get("DISCORD_BOT_TOKEN", "")'))

    def test_assignment_detector_keeps_secret_values_toxic(self):
        redaction = load_script("graveyard_redaction")
        secret = "sk-" + ("e" * 24)

        self.assertTrue(redaction.contains_secret_shape(f"token={secret}"))
        self.assertNotIn(secret, redaction.redact_sensitive_text(f"token={secret}"))
        self.assertIn("<REDACTED>", redaction.redact_sensitive_text(f"token={secret}"))


if __name__ == "__main__":
    unittest.main()

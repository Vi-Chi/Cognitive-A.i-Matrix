import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ai_chi.bus.transports.file_transport import stamp_record_integrity


ROOT = Path(__file__).resolve().parents[2]
CHECKER_PATH = ROOT / "scripts" / "check_ledger_integrity.py"

spec = importlib.util.spec_from_file_location("check_ledger_integrity", CHECKER_PATH)
check_ledger_integrity = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(check_ledger_integrity)


class LedgerIntegrityCheckerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.stream = Path(self.tempdir.name) / "stream.jsonl"

    def write_stream(self, count=3):
        previous = ""
        records = []
        for index in range(count):
            record = {
                "v": 1,
                "sigma": "m.test",
                "payload": {"index": index},
                "dest": "test",
            }
            stamped = stamp_record_integrity(record, prev_fingerprint=previous)
            previous = stamped["fingerprint"]
            records.append(stamped)
        self.stream.write_text(
            "".join(check_ledger_integrity.json.dumps(item, sort_keys=True) + "\n" for item in records),
            encoding="utf-8",
        )
        return records

    def test_clean_stream_passes(self):
        self.write_stream()
        self.assertEqual(check_ledger_integrity.check_stream(self.stream), [])
        result = subprocess.run(
            [sys.executable, str(CHECKER_PATH), str(self.stream)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_deleted_middle_record_fails_chain(self):
        records = self.write_stream()
        self.stream.write_text(
            "".join(check_ledger_integrity.json.dumps(item, sort_keys=True) + "\n" for item in (records[0], records[2])),
            encoding="utf-8",
        )
        problems = check_ledger_integrity.check_stream(self.stream)
        self.assertTrue(any("chain break" in problem for problem in problems))

    def test_partial_tail_is_tolerated(self):
        self.write_stream()
        with self.stream.open("a", encoding="utf-8") as handle:
            handle.write('{"v":1')
        problems = check_ledger_integrity.check_stream(self.stream)
        self.assertTrue(any("partial trailing write" in problem for problem in problems))
        fatal = [problem for problem in problems if "tolerated, not fatal" not in problem]
        self.assertEqual(fatal, [])


if __name__ == "__main__":
    unittest.main()

"""Tests for core LedgerWriter integrity stamps."""
import json
import tempfile
import unittest
from pathlib import Path

from ai_chi.bus import MMessage, Mode
from ai_chi.bus.transports.file_transport import (
    FINGERPRINT_FIELD,
    PREV_FINGERPRINT_FIELD,
    record_fingerprint,
)
from ai_chi.core.ledger.writer import LedgerWriter


class TestLedgerWriterIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ledger_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_record_envelope_stamps_fingerprint_chain(self):
        writer = LedgerWriter(self.ledger_dir)
        first = MMessage(
            sigma="m.belief",
            payload={"state": "first"},
            destination="urbi",
            context={"trust_score": 1.0},
            mode=Mode.WAKE,
            tau=1,
        ).validate()
        second = MMessage(
            sigma="m.belief",
            payload={"state": "second"},
            destination="urbi",
            context={"trust_score": 1.0},
            mode=Mode.WAKE,
            tau=2,
        ).validate()

        path = writer.record_envelope(first)
        writer.record_envelope(second)
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(records[0][PREV_FINGERPRINT_FIELD], "")
        self.assertEqual(records[0][FINGERPRINT_FIELD], record_fingerprint(records[0]))
        self.assertEqual(records[1][PREV_FINGERPRINT_FIELD], records[0][FINGERPRINT_FIELD])
        self.assertEqual(records[1][FINGERPRINT_FIELD], record_fingerprint(records[1]))


if __name__ == "__main__":
    unittest.main()

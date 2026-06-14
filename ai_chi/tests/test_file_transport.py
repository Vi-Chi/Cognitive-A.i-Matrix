"""Tests for FileBackedSigmaTransport"""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from ai_chi.bus import MMessage, Mode
from ai_chi.bus.transports.file_transport import (
    FINGERPRINT_FIELD,
    PREV_FINGERPRINT_FIELD,
    FileBackedSigmaTransport,
    FileTransportError,
    record_fingerprint,
)


class TestFileBackedSigmaTransport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name)
        self.transport = FileBackedSigmaTransport(self.storage_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def envelope(self, index=1):
        return {
            "v": 1,
            "σ": "m.belief",
            "π": {"index": index},
            "δ": "urbi",
            "κ": {"trust_score": 0.9},
            "τ": index,
            "μ": "WAKE",
        }

    def strip_integrity(self, record):
        clean = dict(record)
        clean.pop(FINGERPRINT_FIELD, None)
        clean.pop(PREV_FINGERPRINT_FIELD, None)
        return clean

    def test_initialization_creates_directory(self):
        self.assertTrue(self.storage_path.exists())

    def test_write_and_read_envelope(self):
        envelope = self.envelope()
        self.transport.write_envelope("m.belief", envelope)

        [stored] = list(self.transport.read_stream("m.belief"))
        self.assertEqual(self.strip_integrity(stored), envelope)
        self.assertEqual(stored[PREV_FINGERPRINT_FIELD], "")
        self.assertEqual(stored[FINGERPRINT_FIELD], record_fingerprint(stored))
        self.assertTrue((self.storage_path / "m.belief.jsonl").exists())

    def test_ledger_backend_aliases_append_read_and_tail(self):
        first = self.envelope(1)
        second = self.envelope(2)

        self.transport.append("m.belief", first)
        self.transport.append("m.belief", second)

        stored = list(self.transport.read("m.belief"))
        self.assertEqual([self.strip_integrity(item) for item in stored], [first, second])
        self.assertEqual(
            [self.strip_integrity(item) for item in self.transport.tail("m.belief", 1)],
            [second],
        )
        self.assertEqual(self.transport.tail("m.belief", 0), [])

    def test_multiple_records_preserve_order(self):
        first = self.envelope(1)
        second = self.envelope(2)

        self.transport.write_envelope("m.belief", first)
        self.transport.write_envelope("m.belief", second)

        stored = list(self.transport.read_stream("m.belief"))
        self.assertEqual([self.strip_integrity(item) for item in stored], [first, second])
        self.assertEqual(stored[1][PREV_FINGERPRINT_FIELD], stored[0][FINGERPRINT_FIELD])

    def test_accepts_mmessage_without_mutating_wire_shape(self):
        message = MMessage(
            sigma="m.belief",
            payload={"x": 1},
            destination="urbi",
            mode=Mode.DREAM,
            context={"trust_score": 0.8},
            tau=42,
        ).validate()

        self.transport.write_envelope("m.belief", message)
        [stored] = list(self.transport.read_stream("m.belief"))

        self.assertEqual(self.strip_integrity(stored), message.to_dict())
        self.assertIs(MMessage.from_dict(stored).mode, Mode.DREAM)
        self.assertTrue(self.transport.verify_stream_integrity("m.belief")["ok"])

    def test_missing_stream_returns_empty(self):
        self.assertEqual(list(self.transport.read_stream("missing")), [])

    def test_rejects_unsafe_stream_names(self):
        with self.assertRaises(FileTransportError):
            self.transport.write_envelope("../escape", self.envelope())
        self.assertFalse((self.storage_path.parent / "escape.jsonl").exists())

    def test_rejects_malformed_envelope(self):
        bad = self.envelope()
        del bad["μ"]

        with self.assertRaises(FileTransportError):
            self.transport.write_envelope("m.belief", bad)

    def test_invalid_jsonl_line_raises_with_context(self):
        self.transport.write_envelope("m.belief", self.envelope())
        path = self.storage_path / "m.belief.jsonl"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("{bad json}\n")

        with self.assertRaisesRegex(FileTransportError, "line 2"):
            list(self.transport.read_stream("m.belief"))

    def test_trailing_partial_line_is_skipped_on_read(self):
        self.transport.write_envelope("m.belief", self.envelope(1))
        path = self.storage_path / "m.belief.jsonl"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write('{"v":1')

        stored = list(self.transport.read_stream("m.belief"))

        self.assertEqual(len(stored), 1)
        self.assertEqual(self.strip_integrity(stored[0]), self.envelope(1))

    def test_verify_stream_integrity_detects_reorder(self):
        self.transport.write_envelope("m.belief", self.envelope(1))
        self.transport.write_envelope("m.belief", self.envelope(2))
        path = self.storage_path / "m.belief.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        path.write_text(lines[1] + "\n" + lines[0] + "\n", encoding="utf-8")

        result = self.transport.verify_stream_integrity("m.belief")

        self.assertFalse(result["ok"])
        self.assertTrue(any("prev_fingerprint" in error for error in result["errors"]))

    def test_fsync_is_optional(self):
        durable = FileBackedSigmaTransport(self.storage_path / "durable", fsync=True)
        with patch("ai_chi.bus.transports.file_transport.os.fsync") as fsync:
            durable.write_envelope("m.belief", self.envelope())

        fsync.assert_called_once()


if __name__ == "__main__":
    unittest.main()

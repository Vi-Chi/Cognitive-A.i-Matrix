"""File-Backed Sigma Transport

A zero-dependency, append-only JSONL transport for MΣBUS envelopes.
Designed to persist local ledgers (e.g., Autopoiesis ComputeReceipts)
without requiring external network infrastructure.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ai_chi.bus.transports.protocols import LedgerBackend
from ai_chi.utils.filelock import InterprocessLock


REQUIRED_ENVELOPE_KEYS = frozenset({"v", "σ", "π", "δ", "κ", "τ", "μ"})
SAFE_STREAM_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
FINGERPRINT_FIELD = "fingerprint"
PREV_FINGERPRINT_FIELD = "prev_fingerprint"


class FileTransportError(ValueError):
    """Raised when a stream name or JSONL record is invalid."""


def record_fingerprint(record: Mapping[str, Any]) -> str:
    """Return a SHA-256 fingerprint over a record, excluding its own fingerprint."""
    payload = dict(record)
    payload.pop(FINGERPRINT_FIELD, None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def stamp_record_integrity(record: Mapping[str, Any], *, prev_fingerprint: str = "") -> dict[str, Any]:
    """Return a copy stamped with a previous-link and current fingerprint."""
    stamped = dict(record)
    stamped[PREV_FINGERPRINT_FIELD] = str(prev_fingerprint or "")
    stamped[FINGERPRINT_FIELD] = record_fingerprint(stamped)
    return stamped


class FileBackedSigmaTransport(LedgerBackend):
    """Appends 7-field MΣBUS envelopes to local JSONL files."""

    def __init__(self, storage_dir: Path | str, *, fsync: bool = False):
        self.storage_dir = Path(storage_dir)
        self.fsync = bool(fsync)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _stream_path(self, stream_name: str) -> Path:
        name = str(stream_name).strip()
        if not name:
            raise FileTransportError("stream_name is required")
        if name in {".", ".."} or any(ch not in SAFE_STREAM_CHARS for ch in name):
            raise FileTransportError(f"unsafe stream_name: {stream_name!r}")
        path = self.storage_dir / f"{name}.jsonl"
        root = self.storage_dir.resolve()
        resolved = path.resolve()
        if root != resolved.parent and root not in resolved.parents:
            raise FileTransportError(f"stream escapes storage_dir: {stream_name!r}")
        return path

    @staticmethod
    def _coerce_envelope(envelope: Mapping[str, Any] | Any) -> dict[str, Any]:
        if hasattr(envelope, "to_dict"):
            envelope = envelope.to_dict()
        if not isinstance(envelope, Mapping):
            raise FileTransportError("envelope must be a mapping or expose to_dict()")
        result = dict(envelope)
        missing = REQUIRED_ENVELOPE_KEYS - result.keys()
        if missing:
            raise FileTransportError(f"envelope missing key(s): {', '.join(sorted(missing))}")
        if not isinstance(result["π"], dict):
            raise FileTransportError("envelope π must be a dict")
        if not isinstance(result["κ"], dict):
            raise FileTransportError("envelope κ must be a dict")
        return result


    def write_envelope(self, stream_name: str, envelope: Mapping[str, Any] | Any) -> None:
        """Write a 7-field envelope to the specified stream."""
        record = self._coerce_envelope(envelope)
        path = self._stream_path(stream_name)
        
        with InterprocessLock(path):
            record = stamp_record_integrity(record, prev_fingerprint=self._last_fingerprint(path))
            line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line)
                handle.write("\n")
                handle.flush()
                if self.fsync:
                    os.fsync(handle.fileno())

    def append(self, stream_name: str, record: Mapping[str, Any] | Any) -> None:
        """Append one canonical envelope to a stream."""
        self.write_envelope(stream_name, record)

    def read_stream(self, stream_name: str) -> Iterable[dict[str, Any]]:
        """Yield envelopes from the specified stream."""
        path = self._stream_path(stream_name)
        if not path.exists():
            return
        with path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()
            for line_number, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    parsed = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    is_final_partial = line_number == len(lines) and not line.endswith("\n")
                    if is_final_partial:
                        continue
                    raise FileTransportError(
                        f"invalid JSON in {path.name} line {line_number}: {exc}"
                    ) from exc
                yield self._coerce_envelope(parsed)

    def read(self, stream_name: str) -> Iterable[dict[str, Any]]:
        """Yield envelopes from a stream through the LedgerBackend protocol."""
        return self.read_stream(stream_name)

    def tail(self, stream_name: str, count: int) -> list[dict[str, Any]]:
        """Return the last `count` envelopes from a stream."""
        if count <= 0:
            return []
        return list(self.read_stream(stream_name))[-count:]

    def verify_stream_integrity(self, stream_name: str) -> dict[str, Any]:
        """Verify fingerprints and hash-chain links for a stream."""
        errors: list[str] = []
        previous = ""
        records = 0
        for records, record in enumerate(self.read_stream(stream_name), start=1):
            found_prev = str(record.get(PREV_FINGERPRINT_FIELD, ""))
            found = str(record.get(FINGERPRINT_FIELD, ""))
            expected = record_fingerprint(record)
            if found_prev != previous:
                errors.append(
                    f"line {records}: prev_fingerprint {found_prev!r} != expected {previous!r}"
                )
            if found != expected:
                errors.append(f"line {records}: fingerprint mismatch")
            previous = found
        return {
            "ok": not errors,
            "records": records,
            "head_fingerprint": previous,
            "errors": errors,
        }

    def _last_fingerprint(self, path: Path) -> str:
        if not path.exists():
            return ""
        previous = ""
        with path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError as exc:
                is_final_partial = line_number == len(lines) and not line.endswith("\n")
                if is_final_partial:
                    break
                raise FileTransportError(
                    f"invalid JSON in {path.name} line {line_number}: {exc}"
                ) from exc
            previous = str(parsed.get(FINGERPRINT_FIELD, ""))
        return previous

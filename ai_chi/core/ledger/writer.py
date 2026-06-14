"""Append-only JSONL black-box ledger for canonical MΣBUS messages."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ai_chi.bus import MMessage
from ai_chi.bus.transports.file_transport import FINGERPRINT_FIELD, stamp_record_integrity


class LedgerWriter:
    """Write canonical envelopes to five P0 JSONL streams."""

    STREAMS: tuple[str, ...] = (
        "evidence.jsonl",
        "audit_verdicts.jsonl",
        "predictions.jsonl",
        "outcomes.jsonl",
        "calibration.jsonl",
    )

    ROUTE_MAP: dict[str, str] = {
        "ext.observation": "evidence.jsonl",
        "m.evidence": "evidence.jsonl",
        "sys.health": "evidence.jsonl",
        "m.belief": "audit_verdicts.jsonl",
        "m.urbi.audit": "audit_verdicts.jsonl",
        "m.urbi.dream": "audit_verdicts.jsonl",
        "m.prediction_record": "predictions.jsonl",
        "ext.outcome": "outcomes.jsonl",
        "m.calibration": "calibration.jsonl",
        "cm.alert": "calibration.jsonl",
    }

    def __init__(self, ledger_dir: str | Path = "data/ledger") -> None:
        self.ledger_dir = Path(ledger_dir)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)

    def record_envelope(self, envelope: MMessage) -> Path:
        """Append an MΣBUS message and return the stream path used."""
        envelope.validate()
        target = self.ROUTE_MAP.get(envelope.sigma)
        if target is None:
            raise ValueError(f"Unmapped MΣBUS sigma for ledger: {envelope.sigma}")
        file_path = self.ledger_dir / target
        from ai_chi.utils.filelock import InterprocessLock
        with InterprocessLock(file_path):
            record = stamp_record_integrity(
                envelope.to_dict(),
                prev_fingerprint=self._last_fingerprint(file_path),
            )
            with file_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return file_path

    def retrieve_tail(self, filename: str, lines: int = 10) -> list[dict]:
        file_path = self.ledger_dir / filename
        if not file_path.exists():
            return []
        with file_path.open("r", encoding="utf-8") as f:
            all_lines = f.readlines()
        return [json.loads(line) for line in all_lines[-lines:] if line.strip()]

    def record_many(self, envelopes: Iterable[MMessage]) -> list[Path]:
        return [self.record_envelope(e) for e in envelopes]

    def stream_names(self) -> tuple[str, ...]:
        """The five canonical P0 ledger streams."""
        return self.STREAMS

    def _last_fingerprint(self, file_path: Path) -> str:
        if not file_path.exists():
            return ""
        previous = ""
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                previous = str(record.get(FINGERPRINT_FIELD, ""))
        return previous

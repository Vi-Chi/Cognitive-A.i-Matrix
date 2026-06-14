"""DreamScheduler — turns the DREAM Replay Auditor into a standing consolidation pass.

Buffers `m.prediction_record` cognition (from the SMTIS bridge, Urbi, or any producer) and
runs one full DREAM cycle when triggered by any of:
  * a `sys.mode` signal with payload {"mode": "DREAM"} (the system entering DREAM),
  * a buffer threshold (auto-consolidate every N records),
  * a manual `tick()` / `run_cycle()`.

Deterministic and thread-free: triggers are explicit, so it is fully testable. On a cycle it
emits the `m.urbi.dream` report (cognition, μ=DREAM). It complements the bus-driven
`DreamConsolidator` (which patches m.belief from ext.outcome); this one runs the richer
replay→contradiction→consolidation auditor over a record batch.
"""
from __future__ import annotations

import logging
from typing import Optional

from ai_chi.bus import MembraneBus, Mode, MMessage, PredictionRecord
from ai_chi.urbi.dream.auditor import DreamReplayAuditor
from ai_chi.urbi.dream.records import DreamCycleReport
from ai_chi.urbi.dream.replay import prediction_record_from_payload

_LOG = logging.getLogger(__name__)


class DreamScheduler:
    def __init__(self, bus: Optional[MembraneBus] = None, *,
                 auditor: Optional[DreamReplayAuditor] = None,
                 threshold: Optional[int] = None, auto_emit: bool = True) -> None:
        self.bus = bus
        self.auditor = auditor or DreamReplayAuditor()
        self.threshold = threshold
        self.auto_emit = auto_emit
        self._buffer: list[PredictionRecord] = []
        self.last_report: Optional[DreamCycleReport] = None
        if bus is not None:
            bus.subscribe("m.prediction_record", self._on_record)
            bus.subscribe("sys.mode", self._on_mode)

    @property
    def buffered(self) -> int:
        return len(self._buffer)

    def submit(self, rec_or_payload) -> Optional[DreamCycleReport]:
        """Add one record (PredictionRecord or payload dict). Auto-runs at threshold."""
        rec = (rec_or_payload if isinstance(rec_or_payload, PredictionRecord)
               else prediction_record_from_payload(rec_or_payload))
        self._buffer.append(rec)
        if self.threshold is not None and len(self._buffer) >= self.threshold:
            return self.run_cycle()
        return None

    def run_cycle(self, *, clear: bool = True) -> Optional[DreamCycleReport]:
        """Consolidate the buffer now. Returns the report (None if buffer empty)."""
        if not self._buffer:
            return None
        report = self.auditor.run_cycle(self._buffer)
        if self.auto_emit and self.bus is not None:
            self.bus.publish(self.auditor.to_message(report))
        self.last_report = report
        if clear:
            self._buffer = []
        _LOG.info("DREAM cycle: %d records, coherence %.3f→%.3f, exit_ready=%s",
                  report.processed_records, report.coherence_before,
                  report.coherence_after, report.exit_ready)
        return report

    def tick(self) -> Optional[DreamCycleReport]:
        """Manual trigger (alias for run_cycle)."""
        return self.run_cycle()

    # --- bus handlers ----------------------------------------------------
    def _on_record(self, msg: MMessage) -> None:
        try:
            self.submit(msg.payload)
        except Exception:  # a malformed record must not kill the subscriber
            _LOG.exception("DreamScheduler failed to buffer a prediction record")

    def _on_mode(self, msg: MMessage) -> None:
        if str(msg.payload.get("mode", "")).upper() == Mode.DREAM.value:
            self.run_cycle()

"""CAL bus wiring — the subscriber shell for the windowed CalibrationMonitor.

Reconciles the duplicate CAL: `calibration.py` owns the windowed Ω₄ math (unit-tested);
this module is ONLY the MΣBUS wiring. It subscribes `ext.outcome`, delegates to a
CalibrationMonitor, and republishes the resulting `m.calibration` / `cm.alert` envelope.

The async bus path needs the original prediction confidence in the outcome payload
(`original_confidence`, fallback `confidence`). When absent it skips gracefully — the
synchronous path in core/loop.py already passes confidence directly.
"""
from __future__ import annotations

import logging
from typing import Optional

from ai_chi.bus import MMessage, MembraneBus
from ai_chi.core.cal.calibration import CalibrationMonitor

_LOG = logging.getLogger(__name__)


class CalibrationBusMonitor:
    """Subscribe ext.outcome → CalibrationMonitor.evaluate → publish calibration/alert."""

    def __init__(self, bus: MembraneBus, monitor: Optional[CalibrationMonitor] = None) -> None:
        self.bus = bus
        self.monitor = monitor or CalibrationMonitor()
        bus.subscribe("ext.outcome", self._on_outcome)

    def _on_outcome(self, msg: MMessage) -> Optional[MMessage]:
        payload = msg.payload or {}
        conf = payload.get("original_confidence", payload.get("confidence"))
        if conf is None:
            _LOG.debug("ext.outcome without original_confidence — cannot calibrate; skipping")
            return None
        result = self.monitor.evaluate(
            str(payload.get("target_prediction_id", "")),
            float(conf),
            outcome=msg,
            mode=msg.mode,
        )
        self.bus.publish(result)  # m.calibration, or cm.alert on Ω₄ drift
        return result

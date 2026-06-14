"""Observe adapters — physical-world intake onto the MΣBUS membrane.

Canon-correct rewrite of the Gemini draft against the BUILT mebus:
  • MMessage takes no `version` arg (defaults to int PROTOCOL_VERSION).
  • bus.publish(msg) takes the message only and routes by msg.sigma.
  • mode is a Mode enum; the bus holds no mode (there is no get_current_mode()).
  • τ defaults to monotonic_tau() (causal order, not wall clock).

Adapters emit `ext.observation` — dumb streaming data. Urbi subscribes and decides whether
any datum warrants 3-6-9 audit; the adapters never audit or act.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from ai_chi.bus import MMessage, MembraneBus, Mode

_LOG = logging.getLogger(__name__)


def _observation(*, source: str, raw: str, confidence: float, provenance: str,
                 extracted: Optional[dict] = None, mode: Mode = Mode.WAKE) -> MMessage:
    """Build a canonical ext.observation envelope (κ.trust_score carries sensor trust)."""
    payload = {"source": source, "raw_data": raw, "sensor_confidence": confidence}
    if extracted is not None:
        payload["extracted"] = extracted
    return MMessage(
        sigma="ext.observation",
        payload=payload,
        destination="urbi",
        context={"trust_score": confidence, "domain": source, "provenance": [provenance]},
        mode=mode,
    ).validate()


class CM5HostObserver:
    """Polls host (CM5/RPi) thermal state → ext.observation. Background thread, fire-and-forget."""

    def __init__(self, bus: MembraneBus, *, poll_hz: float = 0.2, mode: Mode = Mode.WAKE,
                 thermal_zone: str = "/sys/class/thermal/thermal_zone0/temp") -> None:
        self.bus = bus
        self.poll_interval = 1.0 / poll_hz
        self.mode = mode
        self.thermal_zone = thermal_zone
        self._active = False
        self._thread: Optional[threading.Thread] = None

    def _read_thermal_c(self) -> float:
        try:
            with open(self.thermal_zone, "r", encoding="utf-8") as f:
                return int(f.read().strip()) / 1000.0
        except (FileNotFoundError, ValueError):
            return -99.0

    def poll_once(self) -> MMessage:
        """Read one sample, publish it, return the envelope (also the unit-test entry point)."""
        temp_c = self._read_thermal_c()
        msg = _observation(
            source="hw.cm5.thermal",
            raw=f"edge_temp_c={temp_c}",
            confidence=1.0,  # hardware root truth
            provenance="urn:sys:hw:thermal",
            extracted={"thermal_c": temp_c},
            mode=self.mode,
        )
        self.bus.publish(msg)
        return msg

    def _loop(self) -> None:
        while self._active:
            try:
                self.poll_once()
            except Exception:  # never let a sensor read kill the thread
                _LOG.exception("CM5HostObserver poll failed")
            time.sleep(self.poll_interval)  # isolated poll timing; NOT a τ mutation

    def start(self) -> None:
        self._active = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        _LOG.info("CM5HostObserver live: host telemetry -> ext.observation")

    def stop(self) -> None:
        self._active = False


class MaritimeNMEAObserver:
    """Gateway for vessel datalink (NMEA0183/2000 / Signal K) → ext.observation.

    Called by the Orbi router layer when a sentence arrives. A physical decoder maps
    sentence structure to `extracted` fields later; P0 carries the raw sentence.
    """

    def __init__(self, bus: MembraneBus, *, mode: Mode = Mode.WAKE) -> None:
        self.bus = bus
        self.mode = mode

    def ingest_nmea_sentence(self, sentence: str, *, rx_confidence: float = 0.9) -> MMessage:
        msg = _observation(
            source="sensor.nmea.bus",
            raw=sentence,
            confidence=rx_confidence,
            provenance="urn:maritime:nmea",
            mode=self.mode,
        )
        self.bus.publish(msg)
        return msg


# RF beacon range gate (SMTIS overlay spec: EagleEye RF ≤ 100 km).
SIGINT_RANGE_GATE_KM = 100.0


class SigintMapperObserver:
    """Passive RF / SDR detection intake → ext.observation. RECEIVE-ONLY.

    Read-only situational awareness layer (SMTIS / WorldWideView SigInt). It maps decoded
    passive detections (frequency, bearing, signal strength, classification) onto the
    membrane as dumb observations; Urbi decides if any warrants audit. There is **no
    transmit path** by construction — SMTIS SAFETY §1.3 prohibits un-audited HF/VHF
    transmission, so this class cannot send, only receive. Out-of-gate detections are
    dropped (returns None) to avoid flooding the picture.
    """

    TRANSMIT_PROHIBITED = True  # invariant marker; this class has no send method

    def __init__(self, bus: MembraneBus, *, mode: Mode = Mode.WAKE,
                 range_gate_km: float = SIGINT_RANGE_GATE_KM) -> None:
        self.bus = bus
        self.mode = mode
        self.range_gate_km = range_gate_km

    def ingest_detection(self, *, freq_mhz: float, bearing_deg: Optional[float] = None,
                         dbm: Optional[float] = None, classification: str = "unknown",
                         range_km: Optional[float] = None,
                         rx_confidence: float = 0.6) -> Optional[MMessage]:
        if range_km is not None and range_km > self.range_gate_km:
            return None  # range-gated out
        extracted = {
            "freq_mhz": freq_mhz, "bearing_deg": bearing_deg, "dbm": dbm,
            "classification": classification, "range_km": range_km, "passive": True,
        }
        msg = _observation(
            source="sensor.sigint.rf",
            raw=f"rf freq={freq_mhz}MHz cls={classification} dbm={dbm} brg={bearing_deg}",
            confidence=rx_confidence,
            provenance="urn:sigint:rf:passive",
            extracted=extracted,
            mode=self.mode,
        )
        self.bus.publish(msg)
        return msg

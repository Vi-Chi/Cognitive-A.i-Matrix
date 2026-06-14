"""Reality intake adapters for the P0 loop."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ai_chi.bus import MMessage, Mode


class BaseObserver(ABC):
    """Convert external or physical input into a canonical MΣBUS observation."""

    def __init__(self, domain: str, *, destination: str = "urbi") -> None:
        self.domain = domain
        self.destination = destination

    @abstractmethod
    def observe(self, *args: Any, **kwargs: Any) -> MMessage:
        """Return a validated canonical MΣBUS message."""


class ManualTextObserver(BaseObserver):
    """Wrap user or console text as an ``ext.observation`` message."""

    def __init__(self, domain: str = "observe.console.claim") -> None:
        super().__init__(domain)

    def observe(
        self,
        text_payload: str,
        *,
        provenance: str = "urn:console:manual",
        sensor_confidence: float = 0.9,
        mode: Mode = Mode.WAKE,
    ) -> MMessage:
        payload = {
            "raw_data": text_payload,
            "source_type": "manual_claim",
            "provenance_uri": provenance,
            "sensor_confidence": sensor_confidence,
        }
        context = {
            "trust_score": sensor_confidence,
            "domain": self.domain,
            "provenance": [provenance],
        }
        return MMessage(
            sigma="ext.observation",
            payload=payload,
            destination=self.destination,
            context=context,
            mode=mode,
        ).validate()


class SystemMetricsObserver(BaseObserver):
    """Wrap host thermal state as a canonical observation."""

    def __init__(
        self,
        domain: str = "observe.system.health",
        *,
        thermal_zone_path: str | Path = "/sys/class/thermal/thermal_zone0/temp",
    ) -> None:
        super().__init__(domain)
        self.thermal_zone_path = Path(thermal_zone_path)

    def observe(self, *, mode: Mode = Mode.WAKE) -> MMessage:
        temp_celsius = self._read_temperature()
        payload = {
            "raw_data": f"SYSTEM_METRICS | Temp: {temp_celsius}C | Node Active",
            "source_type": "system_metrics",
            "provenance_uri": "urn:system:localhost:hw_monitor",
            "sensor_confidence": 1.0,
        }
        return MMessage(
            sigma="sys.health",
            payload=payload,
            destination="orbi",
            context={
                "trust_score": 1.0,
                "domain": self.domain,
                "provenance": [payload["provenance_uri"]],
            },
            mode=mode,
        ).validate()

    def _read_temperature(self) -> str:
        if not self.thermal_zone_path.exists():
            return "Not_RPi_Hardware"
        try:
            raw = self.thermal_zone_path.read_text(encoding="utf-8").strip()
            return str(round(int(raw) / 1000.0, 1))
        except Exception:
            return "Unknown_Error"

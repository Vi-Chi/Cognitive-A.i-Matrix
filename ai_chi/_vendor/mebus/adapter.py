"""MΣBUS adapter / translation layer — the membrane that lets the bus transport ANYTHING.

MΣBUS = Membrane(Sigma + EBUS). The Sigma side gives semantics/identity/provenance and
*translation*; this module is that translation surface. An Adapter converts between an
external representation (NMEA, Signal K, JSON/API, GUI state, SDR events, model responses,
files, raw bytes…) and a typed MMessage — same core inside, context-specific surface outside.
That is what makes MΣBUS a transformer / gateway / translator, not merely a message bus.
"""
from __future__ import annotations

import json as _json
from abc import ABC, abstractmethod
from typing import Any

from .protocol import MMessage, Mode


def wrap_external(source: str, payload: dict, *, destination: str = "urbi",
                  mode: Mode = Mode.WAKE, context: dict | None = None) -> MMessage:
    """Gateway passthrough: carry ANY foreign payload verbatim as an `ext.<source>` message.

    ext.* is the universal carrier class — unknown/foreign content crosses the bus
    intact, tagged with its source, until (or unless) a translator gives it a typed form.
    """
    ctx = dict(context or {})
    ctx.setdefault("provenance", [source])
    return MMessage(sigma=f"ext.{source}", payload=payload, destination=destination,
                    mode=mode, context=ctx).validate()


class Adapter(ABC):
    """Bidirectional translator between an external format and MMessage."""
    name: str = "adapter"

    @abstractmethod
    def ingest(self, external: Any, *, mode: Mode = Mode.WAKE) -> MMessage:
        ...

    @abstractmethod
    def emit(self, msg: MMessage) -> Any:
        ...


class AdapterRegistry:
    """The membrane's set of installed translators."""

    def __init__(self) -> None:
        self._by_name: dict[str, Adapter] = {}

    def register(self, adapter: Adapter) -> None:
        self._by_name[adapter.name] = adapter

    def get(self, name: str) -> Adapter:
        return self._by_name[name]

    def ingest(self, name: str, external: Any, *, mode: Mode = Mode.WAKE) -> MMessage:
        return self.get(name).ingest(external, mode=mode)

    def emit(self, name: str, msg: MMessage) -> Any:
        return self.get(name).emit(msg)


class JSONAdapter(Adapter):
    """Simplest universal gateway: JSON/dict in, JSON out, carried as ext.json."""
    name = "json"

    def ingest(self, external: Any, *, mode: Mode = Mode.WAKE) -> MMessage:
        d = external if isinstance(external, dict) else _json.loads(external)
        return wrap_external("json", d, mode=mode)

    def emit(self, msg: MMessage) -> str:
        return _json.dumps(msg.payload, ensure_ascii=False)


class SignalKAdapter(Adapter):
    """Translate a Signal K delta into a typed maritime cognition message (m.state)."""
    name = "signalk"

    def ingest(self, external: dict, *, mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(
            sigma="m.state",
            payload={"path": external.get("path", ""), "value": external.get("value")},
            destination="urbi", mode=mode,
            context={"provenance": [external.get("source", "signalk")], "domain": "maritime.nav"},
        ).validate()

    def emit(self, msg: MMessage) -> dict:
        return {"path": msg.payload.get("path"), "value": msg.payload.get("value")}

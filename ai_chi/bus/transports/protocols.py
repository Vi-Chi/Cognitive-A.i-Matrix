"""Protocols for local MΣBUS persistence and delivery backends."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any, Protocol

from ai_chi.bus import MMessage


class LedgerBackend(Protocol):
    """Append-only persistence backend for canonical MΣBUS envelopes."""

    def append(self, stream_name: str, record: Mapping[str, Any] | Any) -> None:
        """Append one canonical envelope to a named stream."""

    def read(self, stream_name: str) -> Iterable[dict[str, Any]]:
        """Yield canonical envelopes from a named stream in write order."""

    def tail(self, stream_name: str, count: int) -> list[dict[str, Any]]:
        """Return the last `count` canonical envelopes from a named stream."""


class Transport(Protocol):
    """In-process delivery surface that must route through the membrane."""

    def publish(self, msg: MMessage, *, strict: bool = False) -> bool:
        """Publish a message through the membrane gates."""

    def subscribe(self, sigma: str, handler: Callable[[MMessage], Any]) -> None:
        """Subscribe a handler to a sigma route."""

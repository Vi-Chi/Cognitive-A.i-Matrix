"""MΣBUS core NATS federation transport.

Bridges isolated local-node `MembraneBus` traffic across a LAN — e.g. Urbi (CM5)
<-> Orbi (RPi4). `nats-py` is an OPTIONAL dependency: this module imports cleanly
without it (so the wire (de)serialization is unit-testable), and the live bridge
raises a clear error if NATS is missing at construction time.

Wire format is the protocol's own canonical envelope (`MMessage.to_dict` /
`from_dict`), which round-trips the 7 fields and — critically — coerces μ back to a
`Mode` enum. (The previous implementation hand-rolled `__dict__` serialization and
left `mode` as a bare string, which failed `validate()` with InvalidModeError.)
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import urlparse

from ai_chi.bus import MembraneBus, MMessage

try:  # optional dependency
    from nats.aio.client import Client as NATS
    HAS_NATS = True
except Exception:  # pragma: no cover - exercised only without nats installed
    NATS = None
    HAS_NATS = False

_log = logging.getLogger(__name__)

DEFAULT_OUTBOUND_SIGMA_ALLOWLIST = (
    "ext.",
    "m.belief",
    "m.contract",
    "m.evidence",
    "m.pattern",
    "m.prediction_record",
    "m.validation",
    "m.verification_task",
)
_LOOPBACK_HOSTS = {"", "localhost", "127.0.0.1", "::1"}
_AUTH_OPTION_KEYS = {"token", "user", "password", "credentials", "nkeys_seed", "nkey_seed"}
_TLS_OPTION_KEYS = {"tls", "tls_context"}


# ---- pure, testable wire (de)serialization (no NATS needed) ----
def to_wire(msg: MMessage) -> bytes:
    """Serialize an MMessage to its canonical JSON envelope bytes."""
    return json.dumps(msg.to_dict(), ensure_ascii=False, default=str).encode("utf-8")


def from_wire(data: bytes | str) -> MMessage:
    """Reconstruct (and validate) an MMessage from canonical JSON envelope bytes.

    `MMessage.from_dict` coerces μ -> Mode and runs `validate()`, so the result is
    a fully-typed, valid message (mode is a Mode enum, not a string).
    """
    if isinstance(data, (bytes, bytearray)):
        data = data.decode("utf-8")
    return MMessage.from_dict(json.loads(data))


def routing_key(msg: MMessage) -> str:
    """NATS subject for a message: mebus.<σ>."""
    return f"mebus.{msg.sigma}"


def sigma_allowed(sigma: str, allowlist: Iterable[str]) -> bool:
    """Return True when a sigma matches an exact entry or dotted prefix."""
    value = str(sigma)
    for rule in allowlist:
        pattern = str(rule)
        if pattern.endswith(".") and value.startswith(pattern):
            return True
        if value == pattern:
            return True
    return False


def validate_nats_security(nats_url: str, connect_options: Mapping[str, Any] | None = None) -> None:
    """Require auth and TLS options for non-loopback NATS federation URLs."""
    parsed = urlparse(str(nats_url))
    host = (parsed.hostname or "").lower()
    if host in _LOOPBACK_HOSTS:
        return
    options = dict(connect_options or {})
    has_auth = any(options.get(key) for key in _AUTH_OPTION_KEYS)
    has_tls = parsed.scheme == "tls" or any(options.get(key) for key in _TLS_OPTION_KEYS)
    if not has_auth or not has_tls:
        raise ValueError("non-loopback NATS federation requires auth and TLS options")


class NatsTransportBridge:
    """Mirrors local MembraneBus publishes onto NATS and ingests remote ones."""

    def __init__(self, bus: MembraneBus, nats_url: str = "nats://127.0.0.1:4222",
                 cluster_node: str = "urbi_cm5",
                 *,
                 inbound_trust_ceiling: float = 0.5,
                 allow_inbound_actions: bool = False,
                 outbound_sigma_allowlist: Iterable[str] = DEFAULT_OUTBOUND_SIGMA_ALLOWLIST,
                 connect_options: Mapping[str, Any] | None = None):
        validate_nats_security(nats_url, connect_options)
        if not HAS_NATS:
            raise RuntimeError(
                "nats-py is not installed; install it to run the NATS bridge "
                "(`pip install nats-py`). The wire helpers work without it."
            )
        self.bus = bus
        self.nats_url = nats_url
        self.node_id = cluster_node
        self.inbound_trust_ceiling = float(inbound_trust_ceiling)
        self.allow_inbound_actions = bool(allow_inbound_actions)
        self.outbound_sigma_allowlist = tuple(outbound_sigma_allowlist)
        self.connect_options = dict(connect_options or {})
        self.nc = NATS()
        self.active = False
        self.local_publisher = None
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._start_loop, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _start_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect_and_bind())
        if self.active:
            self.loop.run_forever()

    async def _connect_and_bind(self) -> None:
        try:
            await self.nc.connect(self.nats_url, **self.connect_options)
            self.active = True
            _log.info("[%s] MΣBUS NATS bridge established: %s", self.node_id, self.nats_url)
            # Tap local publishes (retain the original for the fallback / inbound path).
            self.local_publisher = self.bus.publish
            self.bus.publish = self._federated_publish
            await self.nc.subscribe("mebus.>", cb=self._inbound)
        except Exception as exc:
            _log.error("[%s] NATS broker unavailable: %s", self.node_id, exc)
            self.active = False

    def _federated_publish(self, msg: MMessage, *, strict: bool = False):
        # Always deliver locally first (original behaviour).
        result = self.local_publisher(msg, strict=strict)
        # Mirror outward unless this message arrived FROM the network (echo guard).
        if (
            self.active
            and not getattr(msg, "_network_bounce", False)
            and sigma_allowed(msg.sigma, self.outbound_sigma_allowlist)
        ):
            asyncio.run_coroutine_threadsafe(
                self.nc.publish(routing_key(msg), to_wire(msg)), self.loop
            )
        return result

    async def _inbound(self, inbound) -> None:
        try:
            msg = from_wire(inbound.data)            # coerces μ -> Mode + validates
            msg = self._attenuate_inbound(msg, str(getattr(inbound, "subject", "unknown")))
            if msg.is_action and not self.allow_inbound_actions:
                _log.warning("dropping inbound action-layer federation message: %s", msg.sigma)
                return
            setattr(msg, "_network_bounce", True)    # prevent re-broadcast echo
            self.local_publisher(msg)                # original publish, not the federated one
        except Exception as exc:
            _log.error("membrane protocol error on %s: %s", inbound.subject, exc)

    def _attenuate_inbound(self, msg: MMessage, subject: str) -> MMessage:
        context = dict(msg.context or {})
        asserted_trust = _float_or_default(context.get("trust_score"), default=0.0)
        context["trust_score"] = min(asserted_trust, self.inbound_trust_ceiling)
        context["federated"] = True
        context["federation_subject"] = subject
        context["federation_node"] = self.node_id
        original_provenance = context.get("provenance", [])
        if isinstance(original_provenance, list):
            context["federated_original_provenance"] = [str(item) for item in original_provenance]
        elif original_provenance:
            context["federated_original_provenance"] = [str(original_provenance)]
        context["provenance"] = [f"nats:{self.node_id}", f"subject:{subject}"]
        return MMessage(
            version=msg.version,
            sigma=msg.sigma,
            payload=msg.payload,
            destination=msg.destination,
            context=context,
            tau=msg.tau,
            mode=msg.mode,
        ).validate()

    async def _close(self) -> None:
        if self.active and self.nc is not None:
            await self.nc.close()
            self.active = False

    def stop(self) -> None:
        if self.local_publisher is not None:
            self.bus.publish = self.local_publisher
        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._close(), self.loop)


def _float_or_default(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

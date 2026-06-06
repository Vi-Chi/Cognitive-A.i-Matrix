"""MΣBUS protocol core — the seven-field membrane message and the mode-gated bus.

M := (v, σ, π, δ, κ, τ, μ)        (Vi-Chi/MEBUS ARCHITECTURE.md)
  v  version     int   protocol schema version
  σ  signature   str   payload schema / message-type id  ("cm.propose", "m.prediction_record")
  π  payload     dict  message content
  δ  destination str   target module / agent / path      ("cm.wibo835.broadcast", "urbi")
  κ  context     dict  contextual metadata: trust, provenance, expiry (the ΣBUS-CM envelope)
  τ  timestamp   int   monotonic time reference (nanoseconds)
  μ  mode        Mode  system mode {WAKE, LIMINAL, DREAM}

Invariant Ω₈ — action-layer messages are suppressed when μ = DREAM.
Stdlib-only. No third-party dependencies.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

PROTOCOL_VERSION = 1


class Mode(str, Enum):
    WAKE = "WAKE"
    LIMINAL = "LIMINAL"
    DREAM = "DREAM"


# ── Signature namespaces ──────────────────────────────────────────────
# σ is dotted: "<class>.<name>".  Two payload classes reconcile the two buses:
#   cm.*  ΣBUS-CM coordination speech-acts (announce, query, propose, delegate…)
#   m.*   geometric cognition payloads (state, prediction_record…)
#   sys.* bus/system control
#
# Ω₈: the ACTION layer (things that actuate or command) is gated off in DREAM.
ACTION_LAYER_SIGNATURES: frozenset[str] = frozenset({
    "cm.request", "cm.confirm", "cm.fail",      # action speech-acts
    "cm.propose", "cm.agree", "cm.refuse", "cm.retract",  # negotiation → action
    "cm.delegate", "cm.resume",                 # control delegation
    "m.action",                                 # geometric action command
})
ACTION_LAYER_PREFIXES: tuple[str, ...] = ("cmd.",)   # any command path


class MebusError(Exception):
    """Base class for all MΣBUS errors."""


class SchemaVersionError(MebusError):
    pass


class InvalidModeError(MebusError):
    pass


class MessageValidationError(MebusError):
    pass


class DreamActionSuppressed(MebusError):
    """Raised/returned when Ω₈ blocks an action-layer message in DREAM mode."""


def monotonic_tau() -> int:
    """Monotonic timestamp in nanoseconds (τ). Not wall-clock — ordering only."""
    return time.monotonic_ns()


def is_action_layer(sigma: str) -> bool:
    """True if σ denotes an action/actuation message subject to Ω₈."""
    if sigma in ACTION_LAYER_SIGNATURES:
        return True
    return any(sigma.startswith(p) for p in ACTION_LAYER_PREFIXES)


@dataclass
class MMessage:
    """The seven-field membrane message."""
    sigma: str                       # σ — payload schema / type id
    payload: dict                    # π — content
    destination: str                 # δ — target
    mode: Mode = Mode.WAKE           # μ — system mode
    context: dict = field(default_factory=dict)   # κ — trust/provenance/expiry
    tau: int = field(default_factory=monotonic_tau)  # τ — monotonic ns
    version: int = PROTOCOL_VERSION  # v — protocol version

    # ── validation ──────────────────────────────────────────────
    def validate(self) -> "MMessage":
        if self.version != PROTOCOL_VERSION:
            raise SchemaVersionError(
                f"Expected v={PROTOCOL_VERSION}, got v={self.version}"
            )
        if not isinstance(self.mode, Mode):
            raise InvalidModeError(f"μ must be a Mode, got {type(self.mode).__name__}")
        if not self.sigma or "." not in self.sigma:
            raise MessageValidationError(f"σ must be a dotted schema id, got {self.sigma!r}")
        if not isinstance(self.payload, dict):
            raise MessageValidationError("π (payload) must be a dict")
        if not self.destination:
            raise MessageValidationError("δ (destination) is required")
        if not isinstance(self.tau, int):
            raise MessageValidationError("τ (timestamp) must be an int (ns)")
        return self

    @property
    def is_action(self) -> bool:
        return is_action_layer(self.sigma)

    # ── serialisation ───────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "v": self.version,
            "σ": self.sigma,
            "π": self.payload,
            "δ": self.destination,
            "κ": self.context,
            "τ": self.tau,
            "μ": self.mode.value,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MMessage":
        return cls(
            version=d["v"],
            sigma=d["σ"],
            payload=d["π"],
            destination=d["δ"],
            context=d.get("κ", {}),
            tau=d["τ"],
            mode=Mode(d["μ"]),
        ).validate()

    def fingerprint(self) -> str:
        """Deterministic content hash for audit logs."""
        blob = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# ── The mode-gated membrane bus ────────────────────────────────────
class MembraneBus:
    """In-process MΣBUS reference router.

    Enforces Invariant Ω₈: when μ = DREAM, action-layer messages are suppressed
    (never delivered to handlers). LIMINAL is delivered but flagged advisory.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[MMessage], Any]]] = {}
        self.audit_log: list[dict] = []

    def subscribe(self, sigma: str, handler: Callable[[MMessage], Any]) -> None:
        self._handlers.setdefault(sigma, []).append(handler)

    def publish(self, msg: MMessage, *, strict: bool = False) -> bool:
        """Validate, apply Ω₈, and route. Returns True if delivered.

        Ω₈: action-layer message in DREAM → suppressed.
          strict=True  → raise DreamActionSuppressed
          strict=False → drop silently (audited), return False
        """
        msg.validate()
        suppressed = msg.mode == Mode.DREAM and msg.is_action
        self.audit_log.append({
            "fingerprint": msg.fingerprint(),
            "σ": msg.sigma, "δ": msg.destination,
            "μ": msg.mode.value, "suppressed": suppressed, "τ": msg.tau,
        })
        if suppressed:
            if strict:
                raise DreamActionSuppressed(
                    f"Ω₈: action σ={msg.sigma!r} suppressed in DREAM"
                )
            return False
        for handler in self._handlers.get(msg.sigma, []):
            handler(msg)
        return True

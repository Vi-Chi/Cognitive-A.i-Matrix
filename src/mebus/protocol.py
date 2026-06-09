"""MΣBUS protocol core — the seven-field membrane message and the mode-gated bus.

M := (v, σ, π, δ, κ, τ, μ)        (Vi-Chi/MEBUS ARCHITECTURE.md)
  v  version     int   protocol schema version
  σ  signature   str   payload schema / message-type id  ("cm.propose", "m.prediction_record", "ext.nmea")
  π  payload     dict  message content
  δ  destination str   target module / agent / path      ("cm.wibo835.broadcast", "urbi")
  κ  context     dict  contextual metadata: trust, provenance, expiry (the ΣBUS-CM envelope)
  τ  timestamp   int   monotonic time reference (nanoseconds)
  μ  mode        Mode  system mode {WAKE, LIMINAL, DREAM}

Invariant Ω₈ — action-layer messages are suppressed when μ = DREAM.

Beyond canonical v0.1 (recovered from ΣBUS_CM.txt origin spec, additive — see
docs/SIGMABUS_CM_GAP_REVIEW.md):
  * effective-trust gate    — discard below TRUST_FLOOR (κ.trust_score / anomaly / cross_validated)
  * message freshness       — discard when κ.t_expires has passed
  * LIMINAL advisory        — action delivered but flagged advisory (not suppressed)
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
TRUST_FLOOR = 0.1          # ΣBUS-CM: effective trust below this is discarded


class Mode(str, Enum):
    WAKE = "WAKE"
    LIMINAL = "LIMINAL"
    DREAM = "DREAM"


# σ is dotted "<class>.<name>". Payload classes unify the buses on one wire:
#   cm.*   ΣBUS-CM coordination speech-acts (announce, query, propose, delegate…)
#   m.*    geometric cognition payloads (state, prediction_record…)
#   ext.*  universal carrier — ANY foreign payload (nmea, signalk, json, sdr, gui…)
#   sys.*  bus/system control
# Ω₈: the ACTION layer (actuation/commands) is gated off in DREAM.
ACTION_LAYER_SIGNATURES: frozenset[str] = frozenset({
    "cm.request", "cm.confirm", "cm.fail",
    "cm.propose", "cm.agree", "cm.refuse", "cm.retract",
    "cm.delegate", "cm.resume",
    "m.action",
})
ACTION_LAYER_PREFIXES: tuple[str, ...] = ("cmd.",)


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


class MessageExpired(MebusError):
    """Raised in strict mode when κ.t_expires has passed."""


class TrustFloorDiscarded(MebusError):
    """Raised in strict mode when effective trust is below TRUST_FLOOR."""


def monotonic_tau() -> int:
    """Monotonic timestamp in nanoseconds (τ). Not wall-clock — ordering only."""
    return time.monotonic_ns()


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def effective_trust(base: float, *, age_decay: float = 0.0,
                    anomaly: float = 0.0, cross_validated: bool = False) -> float:
    """ΣBUS-CM effective trust: clamp(base − age_decay − anomaly·0.5 + cross_val_bonus)."""
    bonus = 0.1 if cross_validated else 0.0
    return clamp(base - age_decay - anomaly * 0.5 + bonus)


def is_action_layer(sigma: str) -> bool:
    """True if σ denotes an action/actuation message subject to Ω₈."""
    if sigma in ACTION_LAYER_SIGNATURES:
        return True
    return any(sigma.startswith(p) for p in ACTION_LAYER_PREFIXES)


@dataclass
class MMessage:
    """The seven-field membrane message."""
    sigma: str
    payload: dict
    destination: str
    mode: Mode = Mode.WAKE
    context: dict = field(default_factory=dict)
    tau: int = field(default_factory=monotonic_tau)
    version: int = PROTOCOL_VERSION

    def validate(self) -> "MMessage":
        if self.version != PROTOCOL_VERSION:
            raise SchemaVersionError(f"Expected v={PROTOCOL_VERSION}, got v={self.version}")
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

    @property
    def sigma_class(self) -> str:
        """The payload class: cm / m / ext / sys."""
        return self.sigma.split(".", 1)[0]

    def effective_trust(self) -> float:
        """Effective trust from the κ envelope (defaults: full trust, no anomaly)."""
        k = self.context or {}
        return effective_trust(
            float(k.get("trust_score", 1.0)),
            age_decay=float(k.get("age_decay", 0.0)),
            anomaly=float(k.get("anomaly_score", 0.0)),
            cross_validated=bool(k.get("cross_validated", False)),
        )

    def is_fresh(self, now_ns: int | None = None) -> bool:
        """False once κ.t_expires (ns) has passed; always fresh if unset."""
        exp = (self.context or {}).get("t_expires")
        if exp is None:
            return True
        now = monotonic_tau() if now_ns is None else now_ns
        return now <= int(exp)

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


class MembraneBus:
    """In-process MΣBUS reference router.

    Enforces, in order: Ω₈ (action suppressed in DREAM) · freshness (κ.t_expires) ·
    effective-trust floor (κ trust). LIMINAL action messages are delivered but flagged advisory.
    """

    def __init__(self, *, enforce_trust: bool = True, trust_floor: float = TRUST_FLOOR) -> None:
        self._handlers: dict[str, list[Callable[[MMessage], Any]]] = {}
        self.audit_log: list[dict] = []
        self.enforce_trust = enforce_trust
        self.trust_floor = trust_floor

    def subscribe(self, sigma: str, handler: Callable[[MMessage], Any]) -> None:
        self._handlers.setdefault(sigma, []).append(handler)

    def publish(self, msg: MMessage, *, strict: bool = False) -> bool:
        """Validate, apply Ω₈ + freshness + trust gates, and route. True if delivered."""
        msg.validate()
        now = monotonic_tau()

        suppressed = msg.mode == Mode.DREAM and msg.is_action      # Ω₈
        expired = not msg.is_fresh(now)
        trust = msg.effective_trust()
        trust_blocked = self.enforce_trust and trust < self.trust_floor
        advisory = msg.mode == Mode.LIMINAL and msg.is_action

        delivered = not (suppressed or expired or trust_blocked)
        self.audit_log.append({
            "fingerprint": msg.fingerprint(),
            "σ": msg.sigma, "δ": msg.destination, "μ": msg.mode.value,
            "suppressed": suppressed, "expired": expired,
            "trust": round(trust, 3), "trust_blocked": trust_blocked,
            "advisory": advisory, "delivered": delivered, "τ": msg.tau,
        })

        if not delivered:
            if strict:
                if suppressed:
                    raise DreamActionSuppressed(f"Ω₈: action σ={msg.sigma!r} suppressed in DREAM")
                if expired:
                    raise MessageExpired(f"σ={msg.sigma!r} expired (κ.t_expires passed)")
                if trust_blocked:
                    raise TrustFloorDiscarded(
                        f"σ={msg.sigma!r} effective trust {trust:.3f} < floor {self.trust_floor}")
            return False

        for handler in self._handlers.get(msg.sigma, []):
            handler(msg)
        return True

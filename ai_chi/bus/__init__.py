"""Canonical MΣBUS re-export for A.i Core.

There is intentionally no local bus schema module. The source of truth is
``Ai_Stack/MEBUS/mebus/src/mebus``.
"""
from __future__ import annotations

from ai_chi._paths import ensure_dependency_paths

ensure_dependency_paths()

from mebus import (  # noqa: E402,F401
    MMessage,
    MembraneBus,
    Mode,
    PredictionRecord,
    MebusError,
    MessageValidationError,
    monotonic_tau,
    is_action_layer,
    effective_trust,
    clamp,
    TRUST_FLOOR,
    PROTOCOL_VERSION,
)

__all__ = [
    "MMessage",
    "MembraneBus",
    "Mode",
    "PredictionRecord",
    "MebusError",
    "MessageValidationError",
    "monotonic_tau",
    "is_action_layer",
    "effective_trust",
    "clamp",
    "TRUST_FLOOR",
    "PROTOCOL_VERSION",
]

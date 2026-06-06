"""MΣBUS — Membrane Sigma Bus (reference implementation, v0.1).

The typed message membrane connecting Urbi (inward) and Orbi (outward).
M := (v, σ, π, δ, κ, τ, μ) — see docs/PROTOCOL.md.
"""
from .protocol import (
    PROTOCOL_VERSION,
    Mode,
    MMessage,
    MembraneBus,
    is_action_layer,
    MebusError,
    SchemaVersionError,
    InvalidModeError,
    DreamActionSuppressed,
    MessageValidationError,
    monotonic_tau,
)

__all__ = [
    "PROTOCOL_VERSION", "Mode", "MMessage", "MembraneBus", "is_action_layer",
    "MebusError", "SchemaVersionError", "InvalidModeError",
    "DreamActionSuppressed", "MessageValidationError", "monotonic_tau",
]
__version__ = "0.1.0"

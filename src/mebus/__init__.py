"""MΣBUS — Membrane Sigma Bus (reference implementation, v0.1 + recovered ΣBUS-CM gates + m.* cognition).

MΣBUS = Membrane(Sigma + EBUS): a universal transport / transformer / gateway / translator.
Sigma = semantics, identity, provenance, trust, translation. EBUS = event/job transport.
M := (v, σ, π, δ, κ, τ, μ) — see docs/PROTOCOL.md.
"""
from .protocol import (
    PROTOCOL_VERSION, TRUST_FLOOR, Mode, MMessage, MembraneBus,
    is_action_layer, effective_trust, clamp, monotonic_tau,
    MebusError, SchemaVersionError, InvalidModeError, DreamActionSuppressed,
    MessageValidationError, MessageExpired, TrustFloorDiscarded,
)
from .adapter import Adapter, AdapterRegistry, JSONAdapter, SignalKAdapter, wrap_external
from .adapter_nmea import NMEAAdapter, nmea_checksum
from .cognition import (
    DomainTag, UncertaintyType, UncertaintyDist, CausalRef, CognitionPayload,
)
from .coordination import (
    CMType, CM_MESSAGE_TYPES, Role, TrustClass, RESERVED_DOMAINS, AID, CMMessage,
    cm_broadcast, cm_direct, cm_role, cm_federation, sign, verify, canonical_json, proposal_expired,
)
from .records import PredictionRecord

__all__ = [
    "PROTOCOL_VERSION", "TRUST_FLOOR", "Mode", "MMessage", "MembraneBus",
    "is_action_layer", "effective_trust", "clamp", "monotonic_tau",
    "MebusError", "SchemaVersionError", "InvalidModeError", "DreamActionSuppressed",
    "MessageValidationError", "MessageExpired", "TrustFloorDiscarded",
    "Adapter", "AdapterRegistry", "JSONAdapter", "SignalKAdapter", "wrap_external",
    "NMEAAdapter", "nmea_checksum",
    "DomainTag", "UncertaintyType", "UncertaintyDist", "CausalRef", "CognitionPayload",
    "CMType", "CM_MESSAGE_TYPES", "Role", "TrustClass", "RESERVED_DOMAINS", "AID", "CMMessage",
    "cm_broadcast", "cm_direct", "cm_role", "cm_federation", "sign", "verify", "canonical_json", "proposal_expired",
    "PredictionRecord",
]
__version__ = "0.1.0"

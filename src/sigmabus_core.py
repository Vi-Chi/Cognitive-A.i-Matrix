"""Small reference helpers for SIGMABUS CM v0.1.

This is not a complete implementation. It gives implementors a tiny,
dependency-free shape for constructing CM messages and applying the trust gate
described by the draft specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
from uuid import uuid4


CM_MESSAGE_TYPES = {
    "ANNOUNCE",
    "WITHDRAW",
    "HEARTBEAT",
    "QUERY",
    "INFORM",
    "REQUEST",
    "CONFIRM",
    "FAIL",
    "PROPOSE",
    "AGREE",
    "REFUSE",
    "RETRACT",
    "DELEGATE",
    "RESUME",
    "ALERT",
}

TRUST_FLOOR = 0.1


def now_us() -> int:
    """Return Unix time in microseconds."""

    return int(time() * 1_000_000)


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def effective_trust(
    base_trust: float,
    *,
    anomaly_score: float = 0.0,
    cross_validated: bool = False,
    age_decay: float = 0.0,
) -> float:
    """Apply the v0.1 effective trust equation."""

    validation_bonus = 0.1 if cross_validated else 0.0
    return clamp(base_trust - age_decay - (anomaly_score * 0.5) + validation_bonus)


def is_actionable(message: dict[str, Any], *, age_decay: float = 0.0) -> bool:
    """Return true when a message clears the spec trust floor."""

    trust = message.get("trust", {})
    score = effective_trust(
        float(trust.get("trust_score", 0.0)),
        anomaly_score=float(trust.get("anomaly_score", 0.0)),
        cross_validated=bool(trust.get("cross_validated", False)),
        age_decay=age_decay,
    )
    return score >= TRUST_FLOOR


@dataclass(frozen=True)
class SigmaBusMessage:
    """A semantic-envelope wrapped CM message."""

    msg_type: str
    sender_uid: str
    path: str
    payload: dict[str, Any] = field(default_factory=dict)
    receiver_uid: str | None = None
    priority: int = 4
    trust_score: float = 0.9
    trust_class: str = "agent"
    anomaly_score: float = 0.0
    cross_validated: bool = False
    timestamp_us: int = field(default_factory=now_us)
    msg_id: str = field(default_factory=lambda: str(uuid4()))

    def to_envelope(self) -> dict[str, Any]:
        if self.msg_type not in CM_MESSAGE_TYPES:
            raise ValueError(f"unsupported CM message type: {self.msg_type}")
        if not 1 <= self.priority <= 10:
            raise ValueError("priority must be between 1 and 10")

        cm_payload = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "sender_uid": self.sender_uid,
            "receiver_uid": self.receiver_uid,
            "timestamp_us": self.timestamp_us,
            "priority": self.priority,
            **self.payload,
        }

        return {
            "env_version": "1.0",
            "identity": {
                "msg_id": self.msg_id,
                "path": self.path,
                "schema_id": "sigmabus.cm.message",
                "schema_version": 1,
            },
            "temporal": {
                "t_origin_us": self.timestamp_us,
                "t_received_us": self.timestamp_us,
                "t_expires_us": None,
                "latency_us": 0,
            },
            "provenance": {
                "source_id": self.sender_uid,
                "source_type": "agent",
                "interface": "local",
                "path_history": [self.path],
                "derived_from": [],
                "derivation_fn": None,
            },
            "trust": {
                "trust_score": self.trust_score,
                "trust_class": self.trust_class,
                "cross_validated": self.cross_validated,
                "validators": [],
                "anomaly_score": self.anomaly_score,
            },
            "access": {
                "consumers": ["*"],
                "producer_uid": self.sender_uid,
                "write_authorised": False,
            },
            "retention": {
                "class": "voyage",
                "archive_priority": self.priority,
                "compress": False,
            },
            "operational": {
                "priority": self.priority,
                "data_class": "cm",
                "classification": "routine",
            },
            "signature": None,
            "payload": cm_payload,
            "annotations": {},
        }

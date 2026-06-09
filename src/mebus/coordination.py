"""MΣBUS cm.* coordination layer — AID, the 15 CM message types, and the negotiation envelope.

Recovered from the ΣBUS-CM spec + `sigmabus/schemas/{aid,cm-message}.schema.json`. This is the
`cm.*` half of the bus: how autonomous agents identify themselves (AID), advertise capability and
authority, and exchange typed speech-acts (announce / query / inform / request / propose / agree /
delegate …). Coordination bodies ride inside the MΣBUS envelope's π; trust/provenance project into κ.

Safety properties carried over verbatim:
  * P6 — every PROPOSE MUST carry a fallback (executed autonomously if the TTL expires with no AGREE).
  * P7 — human authority is inalienable (`human_override_path` / `emergency_stop_path` on the AID).
  * ed25519 signing in production (the Rust hot-path `sigma-bus-rust` signs envelopes); this stdlib
    reference provides an HMAC-SHA256 signer for tests/offline use — see `sign()` / `verify()`.

Stdlib-only.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from uuid import uuid4

from .protocol import MMessage, Mode, MessageValidationError, monotonic_tau, is_action_layer


# --- vocabularies -----------------------------------------------------------
class CMType(str, Enum):
    ANNOUNCE = "ANNOUNCE"; WITHDRAW = "WITHDRAW"; HEARTBEAT = "HEARTBEAT"
    QUERY = "QUERY"; INFORM = "INFORM"
    REQUEST = "REQUEST"; CONFIRM = "CONFIRM"; FAIL = "FAIL"
    PROPOSE = "PROPOSE"; AGREE = "AGREE"; REFUSE = "REFUSE"; RETRACT = "RETRACT"
    DELEGATE = "DELEGATE"; RESUME = "RESUME"
    ALERT = "ALERT"


CM_MESSAGE_TYPES: frozenset[str] = frozenset(t.value for t in CMType)


class Role(str, Enum):
    NAVIGATION = "navigation"; ENGINE = "engine"; SAFETY = "safety"
    COMMUNICATIONS = "communications"; POWER = "power"; WEATHER = "weather"
    COMMAND = "command"; GATEWAY = "gateway"; OBSERVER = "observer"; CUSTOM = "custom"


class TrustClass(str, Enum):
    SOVEREIGN = "sovereign"; TRUSTED_PEER = "trusted_peer"; FEDERATED = "federated"
    CLAIMED = "claimed"; ANONYMOUS = "anonymous"


# ΣBUS-CM §4.2 reserved data domains; §4.3 reserved prefixes.
RESERVED_DOMAINS: frozenset[str] = frozenset(
    {"nav", "engine", "power", "comms", "safety", "environment", "agent", "meta", "cmd"})

_UID_RE = re.compile(r"^agt-[a-z0-9_]+-[a-z0-9_]+-[0-9]{3}$")


# --- CM addressing (§4.4) ---------------------------------------------------
def cm_broadcast(platform_id: str) -> str:        return f"cm.{platform_id}.broadcast"
def cm_direct(platform_id: str, uid: str) -> str: return f"cm.{platform_id}.{uid}"
def cm_role(platform_id: str, role: str) -> str:  return f"cm.{platform_id}.role.{role}"
def cm_federation(platform_id: str) -> str:       return f"cm.federation.{platform_id}"


# --- signing (stdlib HMAC reference; production = ed25519 via sigma-bus-rust) ---
def canonical_json(obj: dict) -> bytes:
    """Canonical serialisation for signing: sorted keys, no whitespace (ΣBUS-CM §5.5)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign(obj: dict, key: bytes) -> str:
    """Reference HMAC-SHA256 signature over canonical JSON (excluding any 'signature' field)."""
    body = {k: v for k, v in obj.items() if k != "signature"}
    return "hmac:" + hmac.new(key, canonical_json(body), hashlib.sha256).hexdigest()


def verify(obj: dict, key: bytes) -> bool:
    sig = obj.get("signature")
    if not sig:
        return False
    return hmac.compare_digest(sig, sign(obj, key))


# --- Agent Identity Descriptor (AID) ---------------------------------------
@dataclass
class AID:
    """The agent's verifiable passport (aid.schema.json v1.0, condensed to load-bearing fields)."""
    uid: str
    platform_id: str
    role: Role
    tier: int                                   # 1=rule <100ms, 2=small LLM ~500ms, 3=large LLM 1-5s
    perceives: list = field(default_factory=list)       # path patterns (wildcards ok)
    controls: list = field(default_factory=list)        # exact writable paths (no wildcards)
    reasoning_domains: list = field(default_factory=list)
    cm_message_types: list = field(default_factory=lambda: sorted(CM_MESSAGE_TYPES))
    update_rate_hz: float = 1.0
    offline_capable: bool = True
    trust_class: TrustClass = TrustClass.CLAIMED
    pubkey: Optional[str] = None                        # "base64:..." (ed25519)
    software_version: str = "0.1.0"
    human_override_path: Optional[str] = None
    emergency_stop_path: Optional[str] = None
    aid_version: str = "1.0"
    signature: Optional[str] = None

    def validate(self) -> "AID":
        if not _UID_RE.match(self.uid):
            raise MessageValidationError(f"uid must match agt-<platform>-<role>-NNN, got {self.uid!r}")
        if not 1 <= self.tier <= 3:
            raise MessageValidationError(f"tier must be 1..3, got {self.tier}")
        if not isinstance(self.role, Role):
            raise MessageValidationError("role must be a Role")
        if not isinstance(self.trust_class, TrustClass):
            raise MessageValidationError("trust_class must be a TrustClass")
        for c in self.controls:
            if "*" in c:
                raise MessageValidationError(f"controls paths may not contain wildcards: {c!r}")
        bad = set(self.cm_message_types) - CM_MESSAGE_TYPES
        if bad:
            raise MessageValidationError(f"unknown cm_message_types: {sorted(bad)}")
        return self

    def to_dict(self) -> dict:
        d = asdict(self)
        d["role"] = self.role.value
        d["trust_class"] = self.trust_class.value
        return d

    def sign_with(self, key: bytes) -> "AID":
        self.signature = sign(self.to_dict(), key)
        return self

    def announce(self, *, mode: Mode = Mode.WAKE) -> MMessage:
        """Broadcast this AID as a cm.announce message on the platform."""
        return CMMessage(
            msg_type=CMType.ANNOUNCE, sender_uid=self.uid,
            destination=cm_broadcast(self.platform_id),
            subject="agent.announce", content={"aid": self.to_dict()},
            trust_class=self.trust_class.value, mode=mode,
        ).to_message()


# --- CM message (negotiation envelope) -------------------------------------
@dataclass
class CMMessage:
    """A ΣBUS-CM speech-act, wrapped as a `cm.<type>` MΣBUS message."""
    msg_type: CMType
    sender_uid: str
    destination: str = ""
    receiver_uid: Optional[str] = None
    subject: str = ""
    content: dict = field(default_factory=dict)
    conversation_id: Optional[str] = None
    reply_to: Optional[str] = None
    proposal_id: Optional[str] = None
    proposal_ttl_ns: Optional[int] = None              # τ after which a PROPOSE lapses
    fallback: Optional[dict] = None                    # P6: autonomous action if no AGREE before TTL
    priority: int = 5                                  # 1=emergency … 10=background
    trust_score: float = 0.9
    trust_class: str = "agent"
    mode: Mode = Mode.WAKE

    @property
    def sigma(self) -> str:
        return f"cm.{self.msg_type.value.lower()}"

    def validate(self) -> "CMMessage":
        if not isinstance(self.msg_type, CMType):
            raise MessageValidationError("msg_type must be a CMType")
        if not 1 <= self.priority <= 10:
            raise MessageValidationError("priority must be 1..10")
        # P6 — a negotiable PROPOSE must always carry a safe fallback.
        if self.msg_type is CMType.PROPOSE and not self.fallback:
            raise MessageValidationError("PROPOSE requires a `fallback` (P6 safety property)")
        return self

    def to_message(self) -> MMessage:
        self.validate()
        msg_id = str(uuid4())
        payload = {
            "msg_type": self.msg_type.value, "msg_id": msg_id,
            "sender_uid": self.sender_uid, "receiver_uid": self.receiver_uid,
            "timestamp_us": monotonic_tau() // 1000, "priority": self.priority,
            "subject": self.subject, "content": self.content,
        }
        for k, v in (("conversation_id", self.conversation_id), ("reply_to", self.reply_to),
                     ("proposal_id", self.proposal_id), ("proposal_ttl_ns", self.proposal_ttl_ns),
                     ("fallback", self.fallback)):
            if v is not None:
                payload[k] = v
        ctx = {
            "trust_score": self.trust_score, "trust_class": self.trust_class,
            "provenance": [self.sender_uid], "data_class": "cm",
            "priority": self.priority,
        }
        dest = self.destination or (self.receiver_uid or "cm.broadcast")
        return MMessage(sigma=self.sigma, payload=payload, destination=dest,
                        mode=self.mode, context=ctx).validate()


def proposal_expired(ttl_ns: Optional[int], now_ns: Optional[int] = None) -> bool:
    """True once a PROPOSE's TTL has lapsed — caller then executes the message's `fallback`."""
    if ttl_ns is None:
        return False
    return (monotonic_tau() if now_ns is None else now_ns) > ttl_ns

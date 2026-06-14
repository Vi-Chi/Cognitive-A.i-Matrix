"""MSDT typed machine representations — declarative, inert, audit-gated. Stdlib only."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

from ai_chi.bus import MMessage, Mode

SIGMA_CONTRACT = "m.msdt.contract"   # cognition σ (NOT an action layer)


class RiskClass(str, Enum):
    READ = "read"          # observe-only; no world change
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContractStatus(str, Enum):
    DECLARED = "declared"      # minted, not yet audited
    AUDITED = "audited"        # an Urbi audit signal is attached
    GATED = "gated"            # a gate decided (still action_allowed=False here)
    REPLAYED = "replayed"      # consolidated/replayed in DREAM


class MsdtError(ValueError):
    pass


@dataclass(frozen=True)
class CapabilityDescriptor:
    """A typed, declarative description of a machine capability. Executes nothing."""
    capability_id: str
    verb: str                       # machine verb, e.g. "fs.read", "net.fetch", "model.infer"
    target: str                     # what it acts on (a resource class, not an instance)
    risk_class: RiskClass = RiskClass.HIGH
    reversible: bool = False
    params_schema: dict = field(default_factory=dict)   # typed param contract (names→types)
    required_evidence: tuple = ()   # what an auditor must see before any gate could pass
    provenance: str = ""

    def __post_init__(self):
        if not self.capability_id or "." not in self.verb:
            raise MsdtError(f"capability needs id and dotted verb, got {self.verb!r}")

    def fingerprint(self) -> str:
        blob = json.dumps({"v": self.verb, "t": self.target,
                           "s": sorted(self.params_schema)}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:12]


@dataclass
class ExecutionContract:
    """A typed record of *intent to invoke* a capability. Inert and fail-closed.

    `action_allowed` is always False at the MSDT layer — there is no execution here. The
    contract is a replayable audit object: it can be emitted as cognition and consolidated
    by the DREAM layer, but it can never, by itself, cause an action.
    """
    contract_id: str
    capability_id: str
    requested_params: dict
    mode: Mode = Mode.WAKE
    status: ContractStatus = ContractStatus.DECLARED
    audit_ref: Optional[str] = None        # fingerprint/id of the UrbiAuditSignal, when audited
    action_allowed: bool = False           # invariant: always False at this layer

    def __post_init__(self):
        self.action_allowed = False        # no capability without its gate

    def attach_audit(self, audit_ref: str) -> "ExecutionContract":
        self.audit_ref = audit_ref
        self.status = ContractStatus.AUDITED
        self.action_allowed = False        # auditing never grants action
        return self

    def to_payload(self) -> dict:
        d = asdict(self)
        d["mode"] = self.mode.value
        d["status"] = self.status.value
        d["action_allowed"] = False
        return d

    def to_message(self, *, destination: str = "urbi") -> MMessage:
        """Ride MΣBUS as replayable contract cognition (never an action layer)."""
        msg = MMessage(sigma=SIGMA_CONTRACT, payload=self.to_payload(),
                       destination=destination, mode=self.mode,
                       context={"trust_score": 1.0}).validate()
        if msg.is_action:
            raise AssertionError("MSDT contract must be cognition, not an action layer")
        return msg


class CapabilityRegistry:
    """Holds declared capabilities and mints inert, fail-closed execution contracts."""

    def __init__(self) -> None:
        self._caps: dict[str, CapabilityDescriptor] = {}

    def declare(self, cap: CapabilityDescriptor) -> CapabilityDescriptor:
        if cap.capability_id in self._caps:
            raise MsdtError(f"capability {cap.capability_id!r} already declared")
        self._caps[cap.capability_id] = cap
        return cap

    def get(self, capability_id: str) -> CapabilityDescriptor:
        if capability_id not in self._caps:
            raise MsdtError(f"unknown capability {capability_id!r}")
        return self._caps[capability_id]

    def propose_contract(self, capability_id: str, params: dict, *,
                         mode: Mode = Mode.WAKE) -> ExecutionContract:
        """Mint an inert contract. Validates params against the capability's schema names.

        Returns a contract with action_allowed=False. It does not, and cannot, execute.
        """
        cap = self.get(capability_id)
        unknown = set(params) - set(cap.params_schema)
        if unknown:
            raise MsdtError(f"params {sorted(unknown)} not in {capability_id!r} schema")
        cid = hashlib.sha256(
            f"{capability_id}|{json.dumps(params, sort_keys=True)}|{mode.value}".encode()
        ).hexdigest()[:12]
        return ExecutionContract(contract_id=cid, capability_id=capability_id,
                                 requested_params=dict(params), mode=mode)

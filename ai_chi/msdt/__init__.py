"""MSDT — Machine Specification Decoder/Translator (AION-MK seed). RADAR / P0.

The forward-design thesis (from AION_MSDT_MACHINE_KERNEL): the target is **machine language,
not natural language** — a universal *machine control plane*, not one universal model. The
plane is built from typed machine representations: capability descriptors, execution
contracts, and replayable audit records.

This P0 seed encodes that principle in its inert, governance-only form:
  * `CapabilityDescriptor` — a typed, declarative description of a machine capability. It
    does NOT execute anything.
  * `ExecutionContract` — a typed record of *intent to invoke* a capability, carrying its
    audit link and mode. `action_allowed` is ALWAYS False at this layer (no capability
    without its gate); only a real gate — not built here — could ever flip it.
  * `CapabilityRegistry` — declared capabilities; `propose_contract` mints an inert,
    fail-closed contract that rides MΣBUS as replayable cognition.

Nothing in MSDT runs code, calls tools, or alters world state. It is the machine-language
analogue of the Triad doctrine: describe + audit + gate, never act from here.
"""
from ai_chi.msdt.gate import CapabilityGate, CapabilityGateDecision, CapabilityVerdict
from ai_chi.msdt.descriptors import (
    CapabilityDescriptor, ExecutionContract, ContractStatus, RiskClass,
    CapabilityRegistry, MsdtError, SIGMA_CONTRACT,
)

__all__ = [
    "CapabilityDescriptor", "ExecutionContract", "ContractStatus", "RiskClass",
    "CapabilityRegistry", "MsdtError", "SIGMA_CONTRACT",
    "CapabilityGate", "CapabilityGateDecision", "CapabilityVerdict",
]

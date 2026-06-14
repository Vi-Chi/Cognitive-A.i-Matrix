"""MSDT Capability Gate — the boundary between an audited contract and real execution.

Two gates in series, MSDT never executes (ADR: MSDT_CAPABILITY_GATE_DESIGN):

    mint → Urbi audit → [THIS GATE: admissibility] → lower to Orbi ActionProposal →
    Orbi PolicyGate (world-action enforcer) → Orbi executor (NOT built)

`CapabilityGate.evaluate(...)` decides ELIGIBILITY only. Even an ADMIT decision carries
`action_allowed = False`: ADMIT means "eligible to be lowered into an ActionProposal and
re-gated by PolicyGate", nothing more. The world-action rules live solely in PolicyGate;
this gate adds the machine-contract checks one level up and lowers to it, never around it.

Fail-closed: missing audit, undeclared capability, unknown params, non-SUPPORT signal, or
DREAM mode never ADMIT. Stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ai_chi.bus import Mode
from ai_chi.msdt.descriptors import (
    CapabilityDescriptor, ExecutionContract, ContractStatus, RiskClass, CapabilityRegistry,
)
from ai_chi.urbi.audit_signal import (
    UrbiAuditSignal, GATE_SUPPORT, GATE_CONTRADICTION, GATE_SUSPENDED,
)
from ai_chi.orbi.schemas import ActionProposal

_HUMAN_RISK = {RiskClass.HIGH, RiskClass.CRITICAL}


class CapabilityVerdict(str, Enum):
    ADMIT = "admit"            # eligible to lower to an ActionProposal (NOT executed)
    REFUSE = "refuse"          # fail-closed denial
    SUSPEND = "suspend"        # genuinely unresolved [=] / evidence outstanding
    NEEDS_HUMAN = "needs_human"  # high-risk or irreversible — held for a human


@dataclass(frozen=True)
class CapabilityGateDecision:
    verdict: CapabilityVerdict
    reason: str
    contract_id: str
    lowered: Optional[ActionProposal] = None   # present only on ADMIT / NEEDS_HUMAN
    action_allowed: bool = False               # invariant: MSDT never grants execution

    @property
    def admitted(self) -> bool:
        return self.verdict is CapabilityVerdict.ADMIT


class CapabilityGate:
    """Decides whether an audited ExecutionContract is eligible to become an action.

    Holds NO executor: there is deliberately no run/execute/call/invoke method here.
    """

    def evaluate(
        self,
        contract: ExecutionContract,
        *,
        audit_signal: Optional[UrbiAuditSignal],
        registry: CapabilityRegistry,
        mode: Mode = Mode.WAKE,
        actor_id: str = "orbi",
        actor_role: str = "orbi",
        human_approved: bool = False,
    ) -> CapabilityGateDecision:
        cid = contract.contract_id

        def stamp(verdict: CapabilityVerdict, reason: str,
                  lowered: Optional[ActionProposal] = None) -> CapabilityGateDecision:
            contract.status = ContractStatus.GATED
            return CapabilityGateDecision(verdict, reason, cid, lowered=lowered)

        # 1. Capability must be declared (typed, known).
        try:
            cap: CapabilityDescriptor = registry.get(contract.capability_id)
        except Exception:
            return stamp(CapabilityVerdict.REFUSE,
                         f"undeclared capability {contract.capability_id!r}")

        # 2. Audit-before-admission. No signal = fail-closed.
        if audit_signal is None:
            return stamp(CapabilityVerdict.REFUSE, "no Urbi audit signal — fail-closed")

        # 3. Ω₈ — contracts are not admitted to action while μ = DREAM.
        if mode is Mode.DREAM:
            return stamp(CapabilityVerdict.REFUSE, "Ω₈: no admission-to-action in DREAM")

        # 4. The audit verdict.
        sig = audit_signal.to_gate_signal()
        if sig == GATE_CONTRADICTION:
            return stamp(CapabilityVerdict.REFUSE, "Urbi veto: contradiction / constitutional violation")
        if sig == GATE_SUSPENDED:
            return stamp(CapabilityVerdict.SUSPEND, "Urbi [=] suspended: insufficient support")
        if sig != GATE_SUPPORT:
            return stamp(CapabilityVerdict.REFUSE, f"no Urbi support (got {sig!r}) — fail-safe stop")

        # 5. Outstanding evidence the auditor asked for must be satisfied first.
        if audit_signal.required_evidence:
            return stamp(CapabilityVerdict.SUSPEND,
                         f"required evidence outstanding: {list(audit_signal.required_evidence)}")

        # 6. Requested params must be within the typed capability schema.
        unknown = set(contract.requested_params) - set(cap.params_schema)
        if unknown:
            return stamp(CapabilityVerdict.REFUSE, f"params {sorted(unknown)} outside capability schema")

        # 7. Risk ceiling / reversibility → human gate.
        lowered = self._lower(contract, cap, actor_id=actor_id, actor_role=actor_role)
        if (cap.risk_class in _HUMAN_RISK or not cap.reversible) and not human_approved:
            return stamp(CapabilityVerdict.NEEDS_HUMAN,
                         f"risk={cap.risk_class.value} reversible={cap.reversible} — human approval required",
                         lowered=lowered)

        # ADMIT — eligible to lower + re-gate at PolicyGate. Still not executed.
        return stamp(CapabilityVerdict.ADMIT,
                     "declared + audited(SUPPORT) + evidence-complete + params-valid + risk-ok",
                     lowered=lowered)

    def _lower(self, contract: ExecutionContract, cap: CapabilityDescriptor, *,
               actor_id: str, actor_role: str) -> ActionProposal:
        """Lower a machine contract into an Orbi ActionProposal for the world-action gate."""
        needs_human = cap.risk_class in _HUMAN_RISK or not cap.reversible
        return ActionProposal(
            actor_id=actor_id,
            action_type=cap.verb,
            target=cap.target,
            args=dict(contract.requested_params),
            actor_role=actor_role,
            risk_level=cap.risk_class.value,
            requires_human_approval=needs_human,
            provenance=[cap.provenance] if cap.provenance else [contract.contract_id],
        )

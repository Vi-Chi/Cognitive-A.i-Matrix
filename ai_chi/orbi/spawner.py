"""Spawner — Orbi's bounded agent/ghost lifecycle, every step gated and ledgered.

Lifecycle (faithful, minimal slice of the docs' 15-step model):

    spawn request -> ledger
      -> Urbi audits the mission intent (audit signal)
      -> PolicyGate clears the spawn (audit · Ω₈ · trust · provenance · human)
      -> [allow] grant tools (narrowed by template) -> run read-only ghost
                 -> ledger result -> terminate -> emit merge candidates (no auto-merge)
      -> [deny/suspend/needs_human] ledger the refusal; nothing runs.

Only Orbi (this Spawner) may instantiate a ghost, grant tools, and write the ledger
(action monopoly). The ghost never owns tools and never merges itself back.
"""
from __future__ import annotations

from typing import Callable, Optional

from ai_chi.bus import MembraneBus, Mode
from ai_chi.orbi import sigma as S
from ai_chi.orbi.ghost import GhostResult, GhostRuntime
from ai_chi.orbi.ledger import OrbiLedger
from ai_chi.orbi.policy_gate import (
    CONTRADICTION, PENDING, SUPPORT, SUSPENDED, Disposition, GateDecision, PolicyGate,
)
from ai_chi.orbi.registry import AgentTemplate, default_registry
from ai_chi.orbi.schemas import (
    ActionProposal, ActionResult, AgentSpawnRequest, GhostInstanceRecord, ToolGrant,
)
from ai_chi.urbi.memory import MemoryStore, negative_matches, procedural_skills

# audit_fn: intent_text -> (verdict, reason), verdict in {"+","-","=",""}.
AuditFn = Callable[[str], tuple[str, str]]
_SIGNAL = {"+": SUPPORT, "-": CONTRADICTION, "=": SUSPENDED, "": PENDING}


class Spawner:
    def __init__(
        self,
        *,
        ledger: OrbiLedger,
        gate: Optional[PolicyGate] = None,
        bus: Optional[MembraneBus] = None,
        registry: Optional[dict[str, AgentTemplate]] = None,
        audit_fn: Optional[AuditFn] = None,
        memory: Optional[MemoryStore] = None,
    ) -> None:
        self.ledger = ledger
        self.gate = gate or PolicyGate()
        self.bus = bus
        self.registry = registry or default_registry()
        self.audit_fn = audit_fn
        self.memory = memory  # optional Urbi memory for negative/procedural consultation

    def _emit(self, msg) -> None:
        self.ledger.record_envelope(msg)
        if self.bus is not None:
            self.bus.publish(msg)

    def spawn(
        self,
        request: AgentSpawnRequest,
        *,
        mode: Mode = Mode.WAKE,
        files: Optional[list[str]] = None,
        human_approved: bool = False,
    ) -> tuple[GhostInstanceRecord, Optional[GhostResult], GateDecision]:
        self._emit(request.to_message(mode=mode))

        template = self.registry.get(request.agent_template)
        if template is None:
            inst = GhostInstanceRecord(template=request.agent_template, mission=request.mission,
                                       status="denied")
            self._emit(inst.to_message(sigma=S.SIGMA_SPAWN_DENIED, mode=mode))
            return inst, None, GateDecision(Disposition.DENY, "unknown template", request.request_id)

        allowed = template.grantable(request.requested_tools)
        instance = GhostInstanceRecord(
            template=template.template_id, mission=request.mission, tier=template.tier,
            level=template.level, allowed_tools=allowed,
            forbidden_tools=sorted(template.forbidden_tools),
            context_refs=request.context_refs, max_steps=request.max_steps,
            max_runtime_minutes=request.max_runtime_minutes, status="created",
        )
        self._emit(instance.to_message(sigma=S.SIGMA_GHOST_SPAWN, mode=mode))

        # Memory consultation — Urbi knowledge makes the gate STRICTER, never permissive.
        if self.memory is not None:
            neg = negative_matches(self.memory, request.mission)
            if neg:
                instance.status = "denied"
                self._emit(instance.to_message(sigma=S.SIGMA_SPAWN_DENIED, mode=mode))
                why = "; ".join(
                    str(r.get("content", {}).get("reason") or r.get("memory_id"))
                    for r in neg[:3])
                return instance, None, GateDecision(
                    Disposition.DENY, f"blocked by negative memory: {why}", request.request_id)
            # Procedural skills are surfaced to the ghost as context (informational; using
            # a skill's tools still needs a normal grant — no capability without its gate).
            instance.available_skills = [
                r.get("memory_id", "") for r in procedural_skills(self.memory, request.mission)]

        # Urbi audits the mission intent.
        verdict, reason = ("", "")
        if self.audit_fn is not None:
            try:
                verdict, reason = self.audit_fn(request.mission)
            except Exception as exc:
                reason = f"audit_error: {exc}"
        audit_signal = _SIGNAL.get(verdict, PENDING)

        # The gate clears (or refuses) the spawn itself as a world-touching action.
        proposal = ActionProposal(
            actor_id="orbi.spawner", action_type="spawn_ghost", target=instance.ghost_id,
            actor_role=request.actor_role, risk_level=request.risk_level,
            requires_human_approval=request.requires_human_approval,
            provenance=["orbi.spawner"],
        )
        decision = self.gate.evaluate(proposal, mode=mode, audit_signal=audit_signal,
                                      trust=1.0, human_approved=human_approved)
        self._emit(ActionResult(proposal_id=proposal.proposal_id,
                                status=decision.disposition.value,
                                disposition_reason=decision.reason).to_message(mode=mode))

        if not decision.allowed:
            instance.status = {"suspend": "denied", "deny": "denied",
                               "needs_human": "awaiting_human"}.get(
                                   decision.disposition.value, "denied")
            self._emit(instance.to_message(sigma=S.SIGMA_SPAWN_DENIED, mode=mode))
            return instance, None, decision

        # Allowed: approve, grant tools, run, terminate, merge-gate.
        instance.status = "active"
        self._emit(instance.to_message(sigma=S.SIGMA_SPAWN_APPROVED, mode=mode))
        self._emit(instance.to_message(sigma=S.SIGMA_INSTANCE_STARTED, mode=mode))
        for tool in allowed:
            self._emit(ToolGrant(grantee_id=instance.ghost_id, tool=tool,
                                 reason="template grant").to_message(mode=mode))

        # The ghost's out-of-grant actions go through the gate with no per-action audit
        # signal -> fail-safe deny (inspection/sim containment).
        def _gate_check(p: ActionProposal) -> GateDecision:
            d = self.gate.evaluate(p, mode=mode, audit_signal=PENDING, trust=1.0)
            self._emit(p.to_message(mode=mode))
            self._emit(ActionResult(proposal_id=p.proposal_id, status=d.disposition.value,
                                    disposition_reason=d.reason).to_message(mode=mode))
            return d

        ghost = GhostRuntime(instance, gate_check=_gate_check)
        result = ghost.run_inspection(files=files)
        self._emit(instance.to_message(sigma=S.SIGMA_GHOST_RESULT, mode=mode))

        # Merge gate: candidates are emitted but NEVER auto-accepted.
        for mc in result.merge_candidates:
            mc.accepted = False
            self._emit(mc.to_message(mode=mode))

        instance.status = "terminated"
        self._emit(instance.to_message(sigma=S.SIGMA_GHOST_TERMINATED, mode=mode))
        self._emit(instance.to_message(sigma=S.SIGMA_INSTANCE_CLOSED, mode=mode))
        return instance, result, decision

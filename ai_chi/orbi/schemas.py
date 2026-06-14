"""Orbi execution records — dataclasses with canonical MΣBUS envelopes.

stdlib-only (dataclasses, like AIDICT). Each record's ``to_message()`` wraps it in
a validated 7-field envelope on the right σ-class.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from ai_chi.bus import MMessage, Mode
from ai_chi.orbi import sigma as S

DEFAULT_DEST = "orbi"
DOMAIN = "orbi.execution"


def _short_hash(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12]


def _ctx(trust: float, provenance: list[str]) -> dict:
    return {"trust_score": max(0.0, min(1.0, float(trust))), "domain": DOMAIN,
            "provenance": list(provenance)}


@dataclass
class AgentSpawnRequest:
    """A request for Orbi to spawn a bounded agent/ghost. Coordination, not action."""

    agent_template: str
    mission: str
    actor_role: str = "orbi"          # who is requesting (action monopoly check)
    requested_tools: list[str] = field(default_factory=list)
    risk_level: str = "low"           # low|medium|high|critical
    requires_human_approval: bool = False
    max_runtime_minutes: int = 30
    max_steps: int = 80
    context_refs: list[str] = field(default_factory=list)
    output_required: list[str] = field(default_factory=list)
    request_id: str = ""

    def __post_init__(self) -> None:
        if not self.request_id:
            self.request_id = "spawn_" + _short_hash(self.agent_template, self.mission)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "AgentSpawnRequest"
        return d

    def to_message(self, *, mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(sigma=S.SIGMA_SPAWN_REQUEST, payload=self.to_payload(),
                        destination="spawn", context=_ctx(0.8, [self.actor_role]),
                        mode=mode).validate()


@dataclass
class GhostInstanceRecord:
    """A bounded virtual self-instance Orbi forks. Temporary, revocable, logged."""

    template: str
    mission: str
    tier: str = "inspection"          # simulation|inspection|execution
    level: int = 1                    # 0 prompt · 1 process · 2 container · 3 vm
    allowed_tools: list[str] = field(default_factory=list)
    forbidden_tools: list[str] = field(default_factory=list)
    context_refs: list[str] = field(default_factory=list)
    max_steps: int = 80
    max_runtime_minutes: int = 30
    status: str = "created"           # created|active|denied|awaiting_human|terminated
    available_skills: list[str] = field(default_factory=list)  # procedural memory surfaced
    ghost_id: str = ""

    def __post_init__(self) -> None:
        if not self.ghost_id:
            self.ghost_id = "ghost_" + _short_hash(self.template, self.mission, self.tier)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "GhostInstanceRecord"
        return d

    def to_message(self, *, sigma: str = S.SIGMA_GHOST_SPAWN, mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(sigma=sigma, payload=self.to_payload(),
                        destination=DEFAULT_DEST, context=_ctx(0.7, [self.template]),
                        mode=mode).validate()


@dataclass
class ToolGrant:
    """Orbi grants a single capability to a ghost/agent. Agents never self-grant."""

    grantee_id: str
    tool: str
    scope: str = "read_only"          # read_only|sandboxed|supervised
    granted: bool = True
    reason: str = ""
    grant_id: str = ""

    def __post_init__(self) -> None:
        if not self.grant_id:
            self.grant_id = "grant_" + _short_hash(self.grantee_id, self.tool, self.scope)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "ToolGrant"
        return d

    def to_message(self, *, mode: Mode = Mode.WAKE) -> MMessage:
        sigma = S.SIGMA_TOOL_GRANT if self.granted else S.SIGMA_TOOL_REVOKED
        return MMessage(sigma=sigma, payload=self.to_payload(),
                        destination=self.grantee_id, context=_ctx(0.9, ["orbi.gate"]),
                        mode=mode).validate()


@dataclass
class ActionProposal:
    """A proposed world-touching action. MUST clear the PolicyGate before execution."""

    actor_id: str
    action_type: str                  # e.g. fs.read, fs.write, shell, net, spawn_ghost
    target: str = ""
    args: dict = field(default_factory=dict)
    actor_role: str = "agent"         # agent|ghost|orbi  (NOT urbi — monopoly)
    risk_level: str = "low"
    requires_human_approval: bool = False
    provenance: list[str] = field(default_factory=list)
    proposal_id: str = ""

    def __post_init__(self) -> None:
        if not self.proposal_id:
            self.proposal_id = "act_" + _short_hash(self.actor_id, self.action_type, self.target)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "ActionProposal"
        return d

    def to_message(self, *, mode: Mode = Mode.WAKE) -> MMessage:
        prov = self.provenance or [self.actor_id]
        return MMessage(sigma=S.SIGMA_ACTION_PROPOSAL, payload=self.to_payload(),
                        destination=DEFAULT_DEST, context=_ctx(0.6, prov),
                        mode=mode).validate()


@dataclass
class ActionResult:
    """The recorded outcome of a gated action (or a refusal)."""

    proposal_id: str
    status: str                       # allowed|denied|suspended|needs_human|executed|error
    disposition_reason: str = ""
    output: Optional[dict] = None
    result_id: str = ""

    def __post_init__(self) -> None:
        if not self.result_id:
            self.result_id = "res_" + _short_hash(self.proposal_id, self.status)

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "ActionResult"
        return d

    def to_message(self, *, mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(sigma=S.SIGMA_ACTION_RESULT, payload=self.to_payload(),
                        destination=DEFAULT_DEST, context=_ctx(0.9, ["orbi.gate"]),
                        mode=mode).validate()


@dataclass
class MergeCandidate:
    """Residue a ghost proposes for promotion. NEVER auto-merged — ΦΔ/human decides."""

    ghost_id: str
    kind: str                         # finding|skill|claim|contradiction|negative_memory
    content: dict = field(default_factory=dict)
    accepted: bool = False            # always False on emission (no auto-merge)
    candidate_id: str = ""

    def __post_init__(self) -> None:
        if not self.candidate_id:
            self.candidate_id = "merge_" + _short_hash(self.ghost_id, self.kind, str(self.content))

    def to_payload(self) -> dict:
        d = asdict(self)
        d["record_type"] = "MergeCandidate"
        return d

    def to_message(self, *, mode: Mode = Mode.WAKE) -> MMessage:
        return MMessage(sigma=S.SIGMA_GHOST_MERGE_CANDIDATE, payload=self.to_payload(),
                        destination="urbi.dream", context=_ctx(0.4, [self.ghost_id]),
                        mode=mode).validate()

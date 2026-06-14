"""Orbi execution-facing σ-class registry + world-touching action classification.

These σ-classes are Orbi's (execution), kept separate from Urbi/AIDICT cognition
classes (constitution §7.4). They are reserved here so the ledger and gate know
them *before* behaviour is built — "no capability without its gate."

Note on Ω₈: mebus's built-in `is_action_layer` recognises its own action set
(`m.action`, `m.action.*`, selected `cm.*` acts, `cmd.*`, `m.actuation*`,
`m.command*`). Orbi's world-touching σ are not in that set, so the bus will not
auto-suppress them in DREAM. That is intentional and non-invasive:
**the PolicyGate is the enforcer of Ω₈ for Orbi actions** (it denies world-touching
proposals when μ = DREAM). The bus remains a second line for recognised action σ.
"""
from __future__ import annotations

# --- agent lifecycle (coordination/cognition — ledgered, not world-touching) ---
SIGMA_SPAWN_REQUEST = "m.agent.spawn_request"
SIGMA_SPAWN_APPROVED = "m.agent.spawn_approved"
SIGMA_SPAWN_DENIED = "m.agent.spawn_denied"
SIGMA_INSTANCE_STARTED = "m.agent.instance_started"
SIGMA_INSTANCE_CLOSED = "m.agent.instance_closed"
SIGMA_TOOL_GRANT = "m.agent.tool_grant"
SIGMA_TOOL_REVOKED = "m.agent.tool_revoked"
SIGMA_ACTION_PROPOSAL = "m.agent.action_proposal"
SIGMA_ACTION_RESULT = "m.agent.action_result"

# --- ghost runtime ---
SIGMA_GHOST_SPAWN = "m.ghost.spawn_request"
SIGMA_GHOST_SNAPSHOT = "m.ghost.context_snapshot"
SIGMA_GHOST_PLAN = "m.ghost.plan"
SIGMA_GHOST_ACTION = "m.ghost.action"
SIGMA_GHOST_RESULT = "m.ghost.result"
SIGMA_GHOST_TERMINATED = "m.ghost.terminated"
SIGMA_GHOST_MERGE_CANDIDATE = "m.ghost.merge_candidate"
SIGMA_GHOST_REJECTED_MERGE = "m.ghost.rejected_merge"

# --- A2A (reserved; gateway lands later, with its gate) ---
SIGMA_A2A_TASK_REQUEST = "m.a2a.task_request"
SIGMA_A2A_ARTIFACT = "m.a2a.artifact_received"

# World-touching σ — proposing any of these requires a full PolicyGate clearance
# (audit-before-action · Ω₈ · trust · provenance · human gate). Everything else is
# coordination/cognition: ledgered and trust-checked, but not gated as action.
ORBI_ACTION_SIGMA: frozenset[str] = frozenset({
    SIGMA_ACTION_PROPOSAL,
    SIGMA_GHOST_ACTION,
    SIGMA_A2A_TASK_REQUEST,
})


def is_orbi_action(sigma: str) -> bool:
    """True if σ denotes a world-touching Orbi action subject to the PolicyGate."""
    return sigma in ORBI_ACTION_SIGMA

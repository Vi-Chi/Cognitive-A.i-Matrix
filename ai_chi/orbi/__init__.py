"""Orbi — the outward 2-4-6-8 execution circuit (greenfield, built to the constitution).

Orbi is Urbi's co-equal peer, **gated by it through MΣBUS** (see
`_PROJECT_KNOWLEDGE_BASE/URBI_ORBI_MEBUS_BALANCE_CONSTITUTION_2026-06-08.md`).

Separation of powers, enforced here:
  * Urbi holds **judgment** (audit signal) — it cannot act.
  * Orbi holds **action** — but every world-touching action must clear the
    `PolicyGate` (audit-before-action · Ω₈ · trust floor · provenance · human gate),
    and Orbi is the *only* layer that may spawn, grant tools, actuate, or write.
  * MΣBUS holds **flow/enforcement** — Orbi never reaches the world except through it.

Action monopoly: agents/ghosts (Omni) never own tools — they **request**, Orbi
**grants** via the gate. Ghosts never auto-merge back (merge gate → ΦΔ).

This v0 ships the constitutional spine (σ registry, schemas, ledger, policy gate)
plus a minimal, read-only inspection ghost. Execution-tier ghosts, A2A/MCP, and the
Urbi sandbox land later — each *with its gate*, per the growth rule.
"""
from __future__ import annotations

from ai_chi.orbi.policy_gate import PolicyGate, GateDecision, Disposition
from ai_chi.orbi.spawner import Spawner
from ai_chi.orbi.ghost import GhostRuntime, GhostResult
from ai_chi.orbi.registry import AgentTemplate, default_registry
from ai_chi.orbi.ledger import OrbiLedger
from ai_chi.orbi.executor import OrbiExecutor

__all__ = [
    "PolicyGate",
    "GateDecision",
    "Disposition",
    "Spawner",
    "GhostRuntime",
    "GhostResult",
    "AgentTemplate",
    "default_registry",
    "OrbiLedger",
    "OrbiExecutor",
]

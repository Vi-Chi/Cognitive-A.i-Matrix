"""Agent/ghost templates + trust tiers.

A template declares default permissions; a spawn request can only *narrow* them
(requested_tools ∩ allowed). Encodes the omni.* templates from the design docs:
Omni is a spawnable advanced agent, never the control plane — bounded, audited,
revocable.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentTemplate:
    template_id: str
    tier: str                          # simulation|inspection|execution
    level: int                         # 0 prompt · 1 process · 2 container · 3 vm
    allowed_tools: frozenset[str] = frozenset()
    forbidden_tools: frozenset[str] = frozenset({
        "shell.write", "net.unrestricted", "maritime.actuation", "credential.read",
    })
    requires_urbi_audit: bool = True
    requires_human_approval_above: str = "medium"   # low<medium<high<critical
    trust_tier: str = "local_sandboxed"

    def grantable(self, requested: list[str]) -> list[str]:
        """Tools that may actually be granted: requested ∩ allowed, minus forbidden."""
        req = set(requested) or set(self.allowed_tools)
        return sorted((req & set(self.allowed_tools)) - set(self.forbidden_tools))


# Default templates. Inspection/simulation tiers are read-only and the safe first
# prototypes the docs recommend; the execution tier is reserved (lands with its gate).
_TEMPLATES: dict[str, AgentTemplate] = {
    "omni.sim.v0": AgentTemplate(
        template_id="omni.sim.v0", tier="simulation", level=0,
        allowed_tools=frozenset(),  # no tools — pure reasoning/plan
    ),
    "omni.inspector.v0": AgentTemplate(
        template_id="omni.inspector.v0", tier="inspection", level=1,
        allowed_tools=frozenset({"fs.read", "ledger.read", "report.write_sandbox"}),
    ),
    "aidict.scout.v0": AgentTemplate(
        template_id="aidict.scout.v0", tier="inspection", level=1,
        allowed_tools=frozenset({"fs.read", "report.write_sandbox"}),
    ),
    # Reserved — not yet spawnable in v0 (needs container isolation + its gate).
    "omni.builder.v0": AgentTemplate(
        template_id="omni.builder.v0", tier="execution", level=2,
        allowed_tools=frozenset({"fs.read", "fs.write_sandbox", "test.run"}),
        requires_human_approval_above="low",
    ),
}


def default_registry(*, include_heralds: bool = True) -> dict[str, AgentTemplate]:
    """The spawnable templates.

    The base omni.* / aidict.* templates are always present. The DPHA Court of
    Heralds is merged in by default (additive — new keys only, existing keys
    untouched); pass ``include_heralds=False`` for the pre-DPHA set.
    """
    registry = dict(_TEMPLATES)
    if include_heralds:
        # Local import avoids a registry <-> herald import cycle.
        from ai_chi.orbi.herald import herald_templates
        registry.update(herald_templates())
    return registry

"""DPHA Heralds — constitution-gated deployment agents.

The six named constitutional heralds (DPHA 12-Fold canon, 2026-06-11):
    Lumen (Herald of Sight,  T0) · Mneme (Herald of Memory, T1) ·
    Logos (Herald of Meaning, T2) · Artifex (Herald of Making, T3) ·
    Noctis (Herald of Night,  T4) · Nomos (Herald of Law,    T5)

Each herald carries a canonical name, title, and memory tier (T0–T5). A
HeraldContract lowers to the existing AgentTemplate via to_template(), so the Court
slots into the registry/spawner with no lifecycle change. stdlib-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet

from ai_chi.bus.realms import CognitiveRealm
from ai_chi.orbi.registry import AgentTemplate

_DEFAULT_FORBIDDEN = frozenset({
    "shell.write", "net.unrestricted", "maritime.actuation", "credential.read",
})


class HeraldArchetype(str, Enum):
    SIGHT = "sight"; MEMORY = "memory"; MEANING = "meaning"
    FORGE = "forge"; SHADOW = "shadow"; LAW = "law"


# Canonical names / titles / memory tiers (DPHA 12-Fold mandala).
HERALD_NAMES: dict[HeraldArchetype, str] = {
    HeraldArchetype.SIGHT: "Lumen", HeraldArchetype.MEMORY: "Mneme",
    HeraldArchetype.MEANING: "Logos", HeraldArchetype.FORGE: "Artifex",
    HeraldArchetype.SHADOW: "Noctis", HeraldArchetype.LAW: "Nomos",
}
HERALD_TITLES: dict[HeraldArchetype, str] = {
    HeraldArchetype.SIGHT: "Herald of Sight", HeraldArchetype.MEMORY: "Herald of Memory",
    HeraldArchetype.MEANING: "Herald of Meaning", HeraldArchetype.FORGE: "Herald of Making",
    HeraldArchetype.SHADOW: "Herald of Night", HeraldArchetype.LAW: "Herald of Law",
}
HERALD_TIERS: dict[HeraldArchetype, str] = {
    HeraldArchetype.SIGHT: "T0", HeraldArchetype.MEMORY: "T1", HeraldArchetype.MEANING: "T2",
    HeraldArchetype.FORGE: "T3", HeraldArchetype.SHADOW: "T4", HeraldArchetype.LAW: "T5",
}


class HeraldContractError(ValueError):
    """Raised when a herald contract violates a DPHA constitutional invariant."""


@dataclass(frozen=True)
class HeraldContract:
    """The specific "Oath" boundaries for an Orbi herald deployment."""

    template_id: str
    archetype: HeraldArchetype
    niche: str
    oath: str
    name: str = ""
    title: str = ""
    memory_tier: str = ""                        # T0..T5 working/episodic/.../salience manifold
    tier: str = "inspection"                     # simulation|inspection|execution (spawn tier)
    level: int = 1
    allowed_realms: FrozenSet[CognitiveRealm] = field(default_factory=frozenset)
    allowed_tools: FrozenSet[str] = field(default_factory=frozenset)
    forbidden_tools: FrozenSet[str] = field(default_factory=lambda: _DEFAULT_FORBIDDEN)
    requires_urbi_audit: bool = True
    requires_prediction_record: bool = True
    requires_human_approval_above: str = "medium"
    jin_benevolence_ceiling: float = 0.5
    makoto_sincerity_floor: float = 0.6
    death_condition: str = ""

    def __post_init__(self):
        object.__setattr__(self, "allowed_tools", frozenset(self.allowed_tools))
        object.__setattr__(self, "forbidden_tools",
                           frozenset(self.forbidden_tools) | _DEFAULT_FORBIDDEN)
        object.__setattr__(self, "allowed_realms",
                           frozenset(CognitiveRealm(r) for r in self.allowed_realms))
        if not self.name:
            object.__setattr__(self, "name", HERALD_NAMES.get(self.archetype, ""))
        if not self.title:
            object.__setattr__(self, "title", HERALD_TITLES.get(self.archetype, ""))
        if not self.memory_tier:
            object.__setattr__(self, "memory_tier", HERALD_TIERS.get(self.archetype, ""))
        if not (0.0 <= self.jin_benevolence_ceiling <= 1.0):
            raise HeraldContractError("jin_benevolence_ceiling must be in [0,1]")
        if self.archetype is HeraldArchetype.SHADOW:
            if CognitiveRealm.EMBODIED in self.allowed_realms:
                raise HeraldContractError(
                    "[DPHA VETO] Shadow herald may not interface the EMBODIED realm")
            for banned in ("promote.core_memory", "fs.write", "maritime.actuation"):
                if banned not in self.forbidden_tools:
                    raise HeraldContractError(
                        f"[DPHA VETO] Shadow herald must forbid '{banned}'")
        if self.archetype is HeraldArchetype.SIGHT:
            if "execute_terminal" not in self.forbidden_tools \
                    and "shell.write" not in self.forbidden_tools:
                raise HeraldContractError(
                    "[DPHA VETO] Sight herald must forbid execution terminals")

    def grantable(self, requested: list[str]) -> list[str]:
        req = set(requested) or set(self.allowed_tools)
        return sorted((req & set(self.allowed_tools)) - set(self.forbidden_tools))

    def to_template(self) -> AgentTemplate:
        return AgentTemplate(
            template_id=self.template_id, tier=self.tier, level=self.level,
            allowed_tools=self.allowed_tools, forbidden_tools=self.forbidden_tools,
            requires_urbi_audit=self.requires_urbi_audit,
            requires_human_approval_above=self.requires_human_approval_above,
            trust_tier="herald_" + (self.name or self.archetype.value).lower(),
        )


COURT_OF_HERALDS: dict[str, HeraldContract] = {
    "h1.sight.v0": HeraldContract(
        template_id="h1.sight.v0", archetype=HeraldArchetype.SIGHT, tier="inspection", level=1,
        niche="Immediate active sensory + file observation processing.",
        oath="I report the field as it appears now. I do not overwrite memory with present urgency.",
        allowed_realms=frozenset({CognitiveRealm.EMBODIED}),
        allowed_tools=frozenset({"fs.read", "ledger.read", "report.write_sandbox"})),
    "h2.memory.v0": HeraldContract(
        template_id="h2.memory.v0", archetype=HeraldArchetype.MEMORY, tier="inspection", level=1,
        niche="Ledger reads and PredictionRecord lineage matching.",
        oath="I retrieve what was. Rollback is allowed, erasure is not.",
        allowed_realms=frozenset({CognitiveRealm.ARCHIVE}),
        allowed_tools=frozenset({"ledger.read", "memory.read"})),
    "h3.meaning.v0": HeraldContract(
        template_id="h3.meaning.v0", archetype=HeraldArchetype.MEANING, tier="inspection", level=1,
        niche="Semantic bridging and symbol tracking (AION routing).",
        oath="I map meaning across domains. Similarity is not proof; I never grant it authority.",
        allowed_realms=frozenset({CognitiveRealm.ARCHIVE, CognitiveRealm.EXTERNAL}),
        allowed_tools=frozenset({"aion.query", "memory.read"})),
    "h4.forge.v0": HeraldContract(
        template_id="h4.forge.v0", archetype=HeraldArchetype.FORGE, tier="execution", level=2,
        niche="Scripts, logic patching, dry-run deployment in a sandbox.",
        oath="I prepare method in the sandbox. Nothing I forge touches the world without its gate.",
        allowed_realms=frozenset({CognitiveRealm.POSSIBILITY, CognitiveRealm.EMBODIED}),
        allowed_tools=frozenset({"fs.read", "fs.write_sandbox", "test.run"}),
        requires_human_approval_above="low"),
    "h5.shadow.v0": HeraldContract(
        template_id="h5.shadow.v0", archetype=HeraldArchetype.SHADOW, tier="simulation", level=2,
        niche="Adversarial anomaly checks and contradiction mapping, isolated from runtime.",
        oath="I hunt failure so the system does not fail. I do not act on paranoia.",
        allowed_realms=frozenset({CognitiveRealm.POSSIBILITY, CognitiveRealm.ARCHIVE}),
        allowed_tools=frozenset({"ledger.read", "sim.exec", "eval.failure_mode"}),
        forbidden_tools=frozenset({"fs.write", "promote.core_memory", "maritime.actuation"}),
        jin_benevolence_ceiling=0.0, death_condition="end of contradiction mapping sequence"),
    "h6.law.v0": HeraldContract(
        template_id="h6.law.v0", archetype=HeraldArchetype.LAW, tier="inspection", level=1,
        niche="Salience mapping, resource and limit tracing.",
        oath="I weigh and bound. I measure cost and limit; I do not seize what I measure.",
        allowed_realms=frozenset({CognitiveRealm.EMBODIED, CognitiveRealm.ARCHIVE}),
        allowed_tools=frozenset({"ledger.read", "metrics.read"})),
}


def herald_templates() -> dict[str, AgentTemplate]:
    """The Court of Heralds, lowered to registry-compatible AgentTemplates."""
    return {tid: contract.to_template() for tid, contract in COURT_OF_HERALDS.items()}


def by_name(name: str):
    """Look up a herald contract by canonical name (Lumen, Mneme, Logos, …)."""
    want = name.strip().lower()
    for contract in COURT_OF_HERALDS.values():
        if contract.name.lower() == want:
            return contract
    return None

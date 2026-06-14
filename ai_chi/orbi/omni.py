"""Omni — the Orbi ghost / super-agent center that governs the Court of Heralds.

Canon (2026-06-11): "Omni = the Orbi ghost/super-agent center governing the six
heralds." Omni is NOT a new power. It is a coordination layer over the existing,
already-gated Orbi spawn lifecycle:

    Omni convenes a named herald (Lumen, Mneme, Logos, Artifex, Noctis, Nomos)
      → runs DPHA governance pre-checks (herald exists; requested realm is within
        the herald's allowed realms; tools narrowed to the herald's grant set)
      → builds a bounded AgentSpawnRequest from the herald contract
      → routes it through the existing Orbi Spawner, where Urbi audits the mission
        and the PolicyGate disposes (audit · Ω₈ · realm · trust · provenance · human).

Separation of powers is preserved: **Omni proposes, the gate disposes, Urbi
judges.** Omni owns no tools, grants nothing, writes no world state, and cannot
bypass MΣBUS or the PolicyGate.

Divergence is preserved: Omni may convene multiple heralds in parallel
(`convene_many`) and never merges or collapses their separate branches/results.

Design split:
  * `plan()` — pure governance/decision. stdlib + herald + realms only (mebus-free,
    fully unit-testable). Returns a `ConveneOrder`.
  * `convene()` — thin gated execution. Lazily builds the real `AgentSpawnRequest`
    and delegates to a `Spawner` (which pulls mebus); injectable for testing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ai_chi.bus.realms import CognitiveRealm, RealmEnvelope
from ai_chi.orbi.herald import COURT_OF_HERALDS, HeraldContract

# Deterministic realm preference when the caller doesn't pin one: act in the
# most-embodied realm the herald is permitted, falling back outward.
_REALM_PREFERENCE = (
    CognitiveRealm.EMBODIED,
    CognitiveRealm.POSSIBILITY,
    CognitiveRealm.ARCHIVE,
    CognitiveRealm.EXTERNAL,
)
# Spawn risk by herald tier (execution heralds touch more, so they cost more gate).
_TIER_RISK = {"simulation": "low", "inspection": "low", "execution": "medium"}


class OmniError(ValueError):
    """Raised when Omni governance refuses to convene a herald."""


@dataclass(frozen=True)
class ConveneOrder:
    """A resolved, governance-checked plan to convene one herald. NOT yet executed.

    This is the auditable output of Omni's decision: which herald, in which realm,
    with which narrowed tools, at what risk. Execution still goes through the gate.
    """
    herald_name: str
    template_id: str
    archetype: str
    mission: str
    origin_realm: CognitiveRealm
    granted_tools: list
    forbidden_tools: list
    tier: str
    risk_level: str
    requires_human_approval_above: str
    realm_context: dict
    oath: str

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["origin_realm"] = self.origin_realm.value
        return d


class OmniCenter:
    """Governs the Court of Heralds; convenes them only through the gated Spawner."""

    def __init__(self, spawner=None, court: dict[str, HeraldContract] | None = None):
        # spawner is injected (Orbi's execution substrate). None = plan-only Omni.
        self.spawner = spawner
        self.court: dict[str, HeraldContract] = dict(court or COURT_OF_HERALDS)

    # ---- inspection ----
    def roster(self) -> list[dict]:
        return [
            {
                "name": c.name,
                "archetype": c.archetype.value,
                "template_id": c.template_id,
                "tier": c.tier,
                "realms": sorted(r.value for r in c.allowed_realms),
                "oath": c.oath,
            }
            for c in self._ordered()
        ]

    def names(self) -> list[str]:
        return [c.name for c in self._ordered()]

    def _ordered(self):
        return sorted(self.court.values(), key=lambda c: c.template_id)

    def resolve(self, herald_name: str) -> HeraldContract:
        want = herald_name.strip().lower()
        for c in self.court.values():
            if c.name.lower() == want or c.template_id == herald_name:
                return c
        raise OmniError(
            f"unknown herald {herald_name!r}; the court is {self.names()}"
        )

    def primary_realm(self, contract: HeraldContract) -> CognitiveRealm:
        for r in _REALM_PREFERENCE:
            if r in contract.allowed_realms:
                return r
        raise OmniError(f"{contract.name} declares no allowed realm")

    # ---- governance (mebus-free, the testable core) ----
    def plan(
        self,
        herald_name: str,
        mission: str,
        *,
        origin_realm: Optional[CognitiveRealm | str] = None,
        requested_tools: Optional[list] = None,
    ) -> ConveneOrder:
        """Resolve + governance-check a convening. Raises OmniError on refusal."""
        if not mission or not mission.strip():
            raise OmniError("a herald may not be convened without a mission")
        contract = self.resolve(herald_name)

        realm = (
            CognitiveRealm(origin_realm)
            if origin_realm is not None
            else self.primary_realm(contract)
        )
        # DPHA boundary: a herald may only operate inside its declared realms.
        if realm not in contract.allowed_realms:
            raise OmniError(
                f"{contract.name} does not operate in realm '{realm.value}'; "
                f"allowed = {sorted(r.value for r in contract.allowed_realms)}"
            )

        tools = contract.grantable(requested_tools or list(contract.allowed_tools))
        env = RealmEnvelope(
            origin_realm=realm,
            claim_type="herald_convene",
            crossing_authority=f"omni.{contract.name.lower()}",
        )
        return ConveneOrder(
            herald_name=contract.name,
            template_id=contract.template_id,
            archetype=contract.archetype.value,
            mission=mission,
            origin_realm=realm,
            granted_tools=tools,
            forbidden_tools=sorted(contract.forbidden_tools),
            tier=contract.tier,
            risk_level=_TIER_RISK.get(contract.tier, "low"),
            requires_human_approval_above=contract.requires_human_approval_above,
            realm_context=env.as_context(),
            oath=contract.oath,
        )

    # ---- gated execution (delegates to the Spawner; never acts directly) ----
    def convene(
        self,
        herald_name: str,
        mission: str,
        *,
        mode=None,
        origin_realm: Optional[CognitiveRealm | str] = None,
        requested_tools: Optional[list] = None,
        files: Optional[list] = None,
        human_approved: bool = False,
        request_cls=None,
    ):
        """Convene one herald through the gated Orbi Spawner. Returns the Spawner's
        (instance, result, decision). Omni adds governance; the gate still gates."""
        if self.spawner is None:
            raise OmniError("Omni has no spawner bound; it coordinates, it does not act")
        order = self.plan(
            herald_name, mission, origin_realm=origin_realm, requested_tools=requested_tools
        )

        cls = request_cls
        if cls is None:  # lazy — only the execution path needs mebus-backed schemas
            from ai_chi.orbi.schemas import AgentSpawnRequest as cls  # noqa: N813

        request = cls(
            agent_template=order.template_id,
            mission=mission,
            actor_role="orbi",
            requested_tools=order.granted_tools,
            risk_level=order.risk_level,
            context_refs=[
                f"omni:{order.herald_name}",
                f"realm:{order.origin_realm.value}",
            ],
        )
        # Make sure the herald is a spawnable template in the spawner's registry.
        if hasattr(self.spawner, "registry") and order.template_id not in self.spawner.registry:
            self.spawner.registry[order.template_id] = self.court[order.template_id].to_template()

        spawn_kwargs = {"files": files, "human_approved": human_approved}
        if mode is not None:
            spawn_kwargs["mode"] = mode
        return self.spawner.spawn(request, **spawn_kwargs)

    def convene_many(self, conveneables: list[dict], **common):
        """Convene several heralds, preserving divergence: each runs and returns its
        own branch; Omni never merges or collapses their results."""
        results = []
        for item in conveneables:
            name = item["herald"]
            mission = item["mission"]
            kw = {k: v for k, v in item.items() if k not in ("herald", "mission")}
            results.append((name, self.convene(name, mission, **{**common, **kw})))
        return results

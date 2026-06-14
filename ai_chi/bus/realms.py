"""Cognitive Realms — the temporal / causal context bound (CM-Realm).

The "Three-Body Temporal Solution": Past (ARCHIVE), Present (EMBODIED), Future
(POSSIBILITY), Outside (EXTERNAL). It prevents hallucinatory bleed — simulation
fictions can never be executed on the world disguised as observed present-state
fact.

Design decision (ratified 2026-06-11, see PROTOTYPE_REVERSE_ENGINEERING):
the realm rides **inside the MΣBUS message context**, NOT as an 8th envelope
field. The canonical 7-field transport ``M := (v, σ, π, δ, κ, τ, μ)`` is
unchanged. ``RealmEnvelope.as_context()`` produces keys that merge into the
existing ``context`` dict that ``orbi.schemas`` already builds.

Law: "No retroactive truth edits. Rollback is allowed. Erasure is forbidden —
causal replay, not time travel." Lineage is tracked via ``causal_tau_parent``;
nothing is silently overwritten.

stdlib-only (dataclasses), matching the house style.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Tuple


class CognitiveRealm(str, Enum):
    ARCHIVE = "archive"          # what was: proven PredictionRecords, frozen lineage
    EMBODIED = "embodied"        # what is: active sensor planes, living execution
    POSSIBILITY = "possibility"  # what may be: dreams, simulated ghosts, forecasts
    EXTERNAL = "external"        # outside observation: web / API / search / RAG intake


class ContaminationRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SEVERE = "severe_quarantine_mandated"


# Authorities permitted to move a claim from EMBODIED into ARCHIVE (memory write).
_ARCHIVE_WRITE_AUTHORITY_PREFIX = "urbi."


@dataclass(frozen=True)
class RealmEnvelope:
    """The boundary schema bridging causality tracking against payload actions.

    Carried inside an MΣBUS message ``context`` (never a new envelope field).
    """

    origin_realm: CognitiveRealm
    claim_type: str = "observation"     # observation | memory_retrieve | dream_eval | external_query
    crossing_authority: str = ""        # which subsystem requested this crossing (e.g. "urbi.audit")
    contamination_risk: ContaminationRisk = ContaminationRisk.LOW
    causal_tau_parent: Optional[str] = None   # lineage root (NO silent overwrites)

    def __post_init__(self):
        # Coerce string inputs to enums (context round-trips through plain dicts/JSON).
        object.__setattr__(self, "origin_realm", CognitiveRealm(self.origin_realm))
        object.__setattr__(self, "contamination_risk", ContaminationRisk(self.contamination_risk))

    # ---- (de)serialization into the MΣBUS context band ----
    def as_context(self) -> dict:
        return {
            "origin_realm": self.origin_realm.value,
            "claim_type": self.claim_type,
            "crossing_authority": self.crossing_authority,
            "contamination_risk": self.contamination_risk.value,
            "causal_parent": self.causal_tau_parent or "orphan",
        }

    @classmethod
    def from_context(cls, ctx: dict[str, Any]) -> "RealmEnvelope":
        return cls(
            origin_realm=CognitiveRealm(ctx.get("origin_realm", CognitiveRealm.EXTERNAL.value)),
            claim_type=str(ctx.get("claim_type", "observation")),
            crossing_authority=str(ctx.get("crossing_authority", "")),
            contamination_risk=ContaminationRisk(ctx.get("contamination_risk", ContaminationRisk.LOW.value)),
            causal_tau_parent=ctx.get("causal_parent") or ctx.get("causal_tau_parent"),
        )

    # ---- the constitutional realm boundary ----
    def validate_actionable_claim(
        self, is_action_request: bool, target_realm: CognitiveRealm = CognitiveRealm.EMBODIED
    ) -> Tuple[bool, str]:
        """Verify the legitimacy of bringing this claim to an action/target layer."""
        target_realm = CognitiveRealm(target_realm)

        # Severe contamination is hard-quarantined regardless of action.
        if self.contamination_risk is ContaminationRisk.SEVERE:
            return False, "realm_violation: severe contamination — hard-quarantined"

        if is_action_request:
            # Dreams/possibility cannot issue physical actions without conversion + Urbi audit.
            if self.origin_realm is CognitiveRealm.POSSIBILITY:
                return False, ("realm_violation: POSSIBILITY [dream/sim] cannot issue a world "
                               "action without conversion to EMBODIED via Urbi audit")
            # External (web/API) claims are evidence, not authority to act.
            if self.origin_realm is CognitiveRealm.EXTERNAL:
                return False, ("realm_violation: EXTERNAL claim is evidence-only; cannot directly "
                               "drive a world action")

        # Embodied present-state cannot rewrite the Archive without Urbi memory authority.
        if (self.origin_realm is CognitiveRealm.EMBODIED
                and target_realm is CognitiveRealm.ARCHIVE
                and not self.crossing_authority.lower().startswith(_ARCHIVE_WRITE_AUTHORITY_PREFIX)):
            return False, ("realm_violation: EMBODIED claim bypassing Urbi memory promotion "
                           "(erasure forbidden, rollback only)")

        return True, "valid_passage"


def realm_action_gate(
    context: dict[str, Any] | None,
    *,
    is_action: bool,
    target_realm: CognitiveRealm = CognitiveRealm.EMBODIED,
) -> Tuple[bool, str]:
    """Backward-compatible gate helper for PolicyGate.

    Reads a RealmEnvelope from a message/proposal ``context`` dict. If no realm is
    declared, returns ``(True, "no realm declared")`` — i.e. existing callers that
    never set a realm see *zero* behaviour change.
    """
    ctx = context or {}
    if "origin_realm" not in ctx:
        return True, "no realm declared"
    return RealmEnvelope.from_context(ctx).validate_actionable_claim(is_action, target_realm)

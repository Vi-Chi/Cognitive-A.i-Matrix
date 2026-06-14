"""DREAM Replay Auditor — record types for the offline consolidation cycle.

The Dream Layer (ΦΔ) consumes PredictionRecords in DREAM and proposes how memory
should be consolidated. It PROPOSES only — it never writes. CORE is the Promoter's
monopoly, so no proposal may target CORE. Divergent outliers are PRESERVED, never
discarded (Axiom 11: compression must preserve structure).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum

from ai_chi.urbi.memory import Tier


class ConsolidationAction(str, Enum):
    PROMOTE = "promote"                  # cross-supported [+]  -> candidacy toward SEMANTIC
    DEMOTE = "demote"                    # contradicted [-]     -> NEGATIVE
    QUARANTINE = "quarantine"            # corruption/violation -> QUARANTINE (sealed, not deleted)
    PRESERVE_OUTLIER = "preserve_outlier"  # divergent [=]      -> kept (Axiom 11)


# An action's proposed destination tier. CORE is intentionally absent: the Dream
# layer is audit-only and may never propose a CORE write (Promoter monopoly).
ACTION_TARGET_TIER: dict[ConsolidationAction, Tier] = {
    ConsolidationAction.PROMOTE: Tier.SEMANTIC,
    ConsolidationAction.DEMOTE: Tier.NEGATIVE,
    ConsolidationAction.QUARANTINE: Tier.QUARANTINE,
    ConsolidationAction.PRESERVE_OUTLIER: Tier.EPISODIC,
}


class ContradictionKind(str, Enum):
    PREDICTION_ERROR = "prediction_error"      # high-confidence-wrong: priority replay target
    BELIEF_CONFLICT = "belief_conflict"        # two records disagree on the same belief key
    SIMULACRUM = "simulacrum"                  # echo chamber: same prediction repeated (Axiom 12)
    UNRESOLVED = "unresolved_uncertainty"      # [=] carrying real error; needs evidence


@dataclass(frozen=True)
class Contradiction:
    claim_id: str
    kind: ContradictionKind
    severity: str                              # low | medium | high
    detail: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


@dataclass(frozen=True)
class ConsolidationProposal:
    claim_id: str
    action: ConsolidationAction
    target_tier: Tier
    epistemic_state: str                       # [+] / [-] / [=]
    reason: str

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "action": self.action.value,
            "target_tier": self.target_tier.value,
            "epistemic_state": self.epistemic_state,
            "reason": self.reason,
        }


@dataclass
class DreamCycleReport:
    """The output of one DREAM consolidation cycle. Cognition, never action."""
    cycle_id: str
    started_at: str
    completed_at: str
    processed_records: int
    coherence_before: float
    coherence_after: float
    contradictions: list = field(default_factory=list)         # list[Contradiction]
    proposals: list = field(default_factory=list)              # list[ConsolidationProposal]
    simulacrum_flags: list = field(default_factory=list)       # list[str] claim_ids/domains
    exit_ready: bool = False

    @property
    def coherence_gain(self) -> float:
        return round(self.coherence_after - self.coherence_before, 6)

    def counts(self) -> dict:
        c: dict[str, int] = {}
        for p in self.proposals:
            c[p.action.value] = c.get(p.action.value, 0) + 1
        return c

    def to_payload(self) -> dict:
        return {
            "cycle_id": self.cycle_id,
            "mode": "DREAM",
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "processed_records": self.processed_records,
            "coherence_before": round(self.coherence_before, 6),
            "coherence_after": round(self.coherence_after, 6),
            "coherence_gain": self.coherence_gain,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "proposals": [p.to_dict() for p in self.proposals],
            "simulacrum_flags": list(self.simulacrum_flags),
            "proposal_counts": self.counts(),
            "exit_ready": self.exit_ready,
            "action_allowed": False,   # DREAM = no world action
        }

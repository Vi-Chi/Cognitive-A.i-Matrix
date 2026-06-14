"""AION ontology primitives: evidence levels, transfer levels, risk, trust, authority.

Stdlib-only. These are the gating axes the rest of AION enforces.
"""
from __future__ import annotations

from enum import Enum, IntEnum


class EvidenceLevel(IntEnum):
    """How strongly a pattern is grounded (AIONCM section 3)."""
    RESEMBLANCE = 0      # things look similar — never authoritative
    STRUCTURAL = 1       # components map cleanly across domains
    BEHAVIORAL = 2       # similar dynamics under observation
    CAUSAL = 3           # similar mechanisms appear to cause similar behavior
    ENGINEERING = 4      # tested and useful in the target system
    CONSTITUTIONAL = 5   # proven necessary for safety/integrity

    @property
    def label(self) -> str:
        return self.name.capitalize()


class TransferLevel(IntEnum):
    """Permission class for moving a pattern across domains (AIONCM section 4)."""
    T0 = 0   # Observe  — store pattern only, no action
    T1 = 1   # Compare  — read-only cross-domain comparison
    T2 = 2   # Simulate — DREAM simulation, offline only
    T3 = 3   # Prototype — sandbox prototype + PredictionRecord
    T4 = 4   # Contract — explicit capability contract; action within contract
    T5 = 5   # Constitutional — global invariant; needs Vi approval + migration

    @property
    def label(self) -> str:
        return {
            0: "Observe", 1: "Compare", 2: "Simulate",
            3: "Prototype", 4: "Contract", 5: "Constitutional",
        }[int(self)]


class RiskClass(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrustState(Enum):
    """Tri-state epistemics. '=' (suspended) is a safety state, not a weak one."""
    PLUS = "+"     # support / affirmative
    MINUS = "-"    # contradiction / adversarial
    EQUALS = "="   # uncertainty / unresolved (default for new/neutral input)


class Sensitivity(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    RESTRICTED = "restricted"


class Authority(Enum):
    """Who may stamp what. Enforces separation of powers at record level."""
    URBI = "urbi"        # may audit/classify/veto
    ORBI = "orbi"        # may execute contracted patterns
    MEBUS = "mebus"      # may enforce/route
    OMNI = "omni"        # may observe/submit (untrusted by default)
    DREAM = "dream"      # may simulate/compare
    HUMAN = "human"      # Vi — approves constitutional change
    CLOUD = "cloud"      # external — evidence only, never authority
    CHAIN = "chain"      # on-chain — proof/hash only, never authority
    UNKNOWN = "unknown"


# Domains whose patterns stay symbolic by default (cap evidence at BEHAVIORAL=2,
# transfer at T1) unless independently grounded. AIONCM section 3 default principle.
SYMBOLIC_DOMAINS = frozenset({
    "religion", "mythology", "myth", "fiction", "science_fiction", "scifi",
    "philosophy", "metaphysics", "simulation_hypothesis", "digital_physics",
    "narrative", "great_works",
})

# Origins that arrive as evidence, never as authority (AIONCM acceptance test 9).
EVIDENCE_ONLY_AUTHORITIES = frozenset({Authority.CLOUD, Authority.CHAIN})


def transfer_ceiling_for_evidence(level: EvidenceLevel) -> TransferLevel:
    """Max transfer level an evidence level may justify.

    Evidence 0 caps at T1 (Compare) — acceptance test 2. Otherwise transfer may
    rise no higher than the matching numeric level.
    """
    if level <= EvidenceLevel.RESEMBLANCE:
        return TransferLevel.T1
    return TransferLevel(int(level))


def is_symbolic(domains) -> bool:
    return any(str(d).strip().lower() in SYMBOLIC_DOMAINS for d in (domains or []))

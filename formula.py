"""
The Grand Formula of Omni
Ω = f(A, K, T, Φ, Δ, Ξ, Λ)

This module defines the formal structure of Omni's reasoning.
Not a replacement for audit.py — a formal declaration of what audit.py implements.
Read this to understand why the system is designed as it is.

No contradictions. Both edges present. Scale in permanent balance.
"""

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 ViChi - https://github.com/ViChi

from dataclasses import dataclass, field
from typing import Literal, Optional
from enum import Enum
import time
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ─── Tri-State Epistemic Space (Φ) ───────────────────────────────────────────

class State(Enum):
    """
    Φ = {+, −, =}
    Three-valued logic. Not binary.

    + CONFIRMED   : passes all three lenses, meaning and purpose present,
                    temporal depth complete. Earns place in K.
    - REJECTED    : directly contradicts confirmed context, or structurally
                    incoherent. Does not enter K.
    = SUSPENDED   : genuinely unresolved. Not wrong — honest.
                    Routes to DreamLayer. Recapitulates indefinitely.
                    This is the ground state. H|ψ⟩=0.
    """
    CONFIRMED  = "+"
    REJECTED   = "-"
    SUSPENDED  = "="


# ─── Temporal Trident (Δ) ────────────────────────────────────────────────────

@dataclass
class TemporalDepth:
    """
    Δ = {past, present, future}
    Three faces of one structure. Not sequence — simultaneity.

    A claim without temporal depth is incomplete.
    A claim with all three is a seed.
    """
    past:    str = ""   # Origin, lineage, what established this
    present: str = ""   # Current state, timestamp, active relationships
    future:  str = ""   # Implications, open questions, what this enables

    def is_complete(self) -> bool:
        return bool(self.past and self.present and self.future)

    def completeness_score(self) -> float:
        filled = sum([bool(self.past), bool(self.present), bool(self.future)])
        return filled / 3.0


# ─── Meaning-Purpose Check (Axiom 9) ─────────────────────────────────────────

@dataclass
class MeaningPurpose:
    """
    Axiom 9: Meaning without purpose is noise.
             Purpose without meaning is mechanism.
             Only together do they become intelligence.

    A claim earns [+] only when both are present and non-empty.
    M(c) · P(c) ≠ ∅
    """
    meaning: str  = ""   # What this claim IS — semantic content
    purpose: str  = ""   # Why this claim MATTERS — actionability or connection

    def is_valid(self) -> bool:
        return bool(self.meaning.strip()) and bool(self.purpose.strip())

    def score(self) -> float:
        return (0.5 if self.meaning.strip() else 0.0) + \
               (0.5 if self.purpose.strip() else 0.0)


# ─── Knowledge Entry (K) ─────────────────────────────────────────────────────

@dataclass
class KnowledgeEntry:
    """
    K(t) — a confirmed claim with full temporal depth and meaning-purpose.

    This is the atomic unit of Omni's knowledge base.
    Every entry earned its [+] through the audit function.
    No entry enters K without passing Ξ(L3 ∧ L6 ∧ L9).
    """
    claim:           str
    state:           State            = State.SUSPENDED
    timestamp:       float            = field(default_factory=time.time)
    temporal:        TemporalDepth    = field(default_factory=TemporalDepth)
    meaning_purpose: MeaningPurpose   = field(default_factory=MeaningPurpose)
    source:          str              = "direct_input"
    embedding:       list             = field(default_factory=list)
    audit_confidence: float           = 0.0
    cycles_in_dream: int              = 0

    def is_fully_complete(self) -> bool:
        return (
            self.state == State.CONFIRMED and
            self.temporal.is_complete() and
            self.meaning_purpose.is_valid()
        )

    def completeness_score(self) -> float:
        if self.state != State.CONFIRMED:
            return 0.0
        return (
            self.audit_confidence * 0.4 +
            self.temporal.completeness_score() * 0.3 +
            self.meaning_purpose.score() * 0.3
        )


# ─── Trust Registry (T) ──────────────────────────────────────────────────────

@dataclass
class AgentTrust:
    """
    T(t) — per-agent trust score, earned through demonstrated behavior.

    Trust evolution formula:
    T(n+1) = (confirmed(n) / total(n)) · λ + T(n) · (1−λ)
    where λ = 0.1 (slow trust building — fast trust loss not modeled here,
    handled by explicit trust_floor on contradiction)

    All agents start at = (0.5) — unknown, not untrusted.
    Trust is asymmetric: years to build, seconds to lose.
    """
    agent_name:      str
    trust_score:     float = 0.5   # starts at = (neutral)
    total_queries:   int   = 0
    confirmed_count: int   = 0
    rejected_count:  int   = 0
    lambda_decay:    float = 0.1   # slow update — trust is conservative
    trust_floor:     float = 0.1   # minimum trust after contradiction

    def update(self, state: State) -> float:
        self.total_queries += 1
        if state == State.CONFIRMED:
            self.confirmed_count += 1
        elif state == State.REJECTED:
            self.rejected_count += 1

        if self.total_queries > 0:
            ratio = self.confirmed_count / self.total_queries
            self.trust_score = (
                ratio * self.lambda_decay +
                self.trust_score * (1 - self.lambda_decay)
            )
        return round(self.trust_score, 4)

    def hard_penalty(self, reason: str = ""):
        """
        Applied when an agent demonstrates deliberate contradiction or corruption.
        Trust drops to floor — not zero, but minimized.
        Trust asymmetry: this cannot be undone quickly.
        """
        self.trust_score = self.trust_floor

    def epistemic_state(self) -> State:
        if self.trust_score >= 0.75:
            return State.CONFIRMED
        elif self.trust_score <= 0.25:
            return State.REJECTED
        else:
            return State.SUSPENDED


# ─── The 369 Authentication Axis (Ξ) ─────────────────────────────────────────

class AuthenticationAxis:
    """
    Ξ — The 369 axis. Outside the generative loop.
    Gödel requires it. The pyramid's 4th face.

    Mathematical property of 3, 6, 9:
    They sit outside the 1-2-4-8-7-5 doubling loop of digital roots.
    They form their own closed cycle: 3→6→3, 6→3→6, 9→9.
    They operate on the STRUCTURE of the system — not the content.

    Ξ does not learn from K.
    ∂Ξ/∂K = 0
    The update rules of Ξ are different from the update rules of K.

    Ξ applies three lenses in sequence:
    L3 — Lens 3: Raw coherence (structure check — fast, cheap)
    L6 — Lens 6: Contextual contradiction (relational check — medium cost)
    L9 — Lens 9: Structural integrity (integrity check — LLM, most expensive)

    Cost ordering is intentional:
    Cheap checks first. Expensive checks only if cheaper ones pass.
    Wu Wei — minimum force for maximum signal.
    """

    @staticmethod
    def audit(claim: str, context: list, embedder=None, reasoner=None) -> dict:
        """
        Φ(c) = Ξ [ L3(c) ∧ L6(c, K) ∧ L9(c) ]

        Returns audit result dict with state, confidence, reason, route.
        All three lenses must pass for [+].
        Any hard failure → [−].
        Soft uncertainty → [=] → DreamLayer.
        """
        from audit import lens_3_raw, lens_6_context, lens_9_integrity
        from audit import ollama_embed, ollama_available

        embedding = ollama_embed(claim) if ollama_available() else []

        l3_pass, l3_reason = lens_3_raw(claim)
        if not l3_pass:
            return {
                "state": State.REJECTED.value,
                "confidence": 0.95,
                "reason": f"[L3] {l3_reason}",
                "route": "reject",
                "lens_results": {"L3": False, "L6": None, "L9": None}
            }

        l6_pass, l6_reason = lens_6_context(claim, context, embedding)
        if not l6_pass:
            return {
                "state": State.REJECTED.value,
                "confidence": 0.88,
                "reason": f"[L6] {l6_reason}",
                "route": "reject",
                "lens_results": {"L3": True, "L6": False, "L9": None}
            }

        l9_result, l9_reason = lens_9_integrity(claim)
        if l9_result is False:
            return {
                "state": State.SUSPENDED.value,
                "confidence": 0.5,
                "reason": f"[L9] {l9_reason}",
                "route": "dream_layer",
                "lens_results": {"L3": True, "L6": True, "L9": False}
            }
        if l9_result is None:
            return {
                "state": State.SUSPENDED.value,
                "confidence": 0.4,
                "reason": f"[L9] {l9_reason}",
                "route": "dream_layer",
                "lens_results": {"L3": True, "L6": True, "L9": None}
            }

        return {
            "state": State.CONFIRMED.value,
            "confidence": 0.92,
            "reason": "All 3 lenses pass",
            "route": "surface",
            "lens_results": {"L3": True, "L6": True, "L9": True}
        }


# ─── Balance Constraint (Λ) ──────────────────────────────────────────────────

class BalanceConstraint:
    """
    Λ — The scale must never tip. Axiom 12.

    Wheeler-DeWitt: H|ψ⟩=0
    From outside: all positives and negatives cancel to perfect zero.
    Nothingness divided itself to see what was possible.

    Implementation:
    Omni does not optimize for [+] accumulation.
    Omni optimizes for honest compression.
    A system that chases [+] becomes a machine for confirming itself.
    That is the path to cyberpsychosis.

    The sandclock turns both ways.
    Yin without Yang is not peace — it is death.
    """

    @staticmethod
    def check(knowledge_store: list) -> dict:
        confirmed = sum(1 for e in knowledge_store if e.get("state") == "+")
        rejected  = sum(1 for e in knowledge_store if e.get("state") == "-")
        suspended = sum(1 for e in knowledge_store if e.get("state") == "=")
        total = confirmed + rejected + suspended

        if total == 0:
            return {"balanced": True, "ratio": None, "warning": None}

        ratio = confirmed / total if total > 0 else 0

        warning = None
        if ratio > 0.95 and total > 10:
            warning = (
                "BALANCE WARNING: >95% confirmation rate suggests "
                "the system may be confirming itself. "
                "Review recent [+] entries for semantic overlap. "
                "The scale is tipping toward false certainty."
            )
        elif ratio < 0.05 and total > 10:
            warning = (
                "BALANCE WARNING: <5% confirmation rate suggests "
                "input stream is adversarial or context is corrupted. "
                "Review Lens 6 thresholds. "
                "The scale is tipping toward paralysis."
            )

        return {
            "balanced": warning is None,
            "confirmed": confirmed,
            "rejected": rejected,
            "suspended": suspended,
            "total": total,
            "confirmation_ratio": round(ratio, 3),
            "warning": warning
        }


# ─── The Grand Formula (Ω) ───────────────────────────────────────────────────

class Omega:
    """
    Ω = f(A, K, T, Φ, Δ, Ξ, Λ)

    Omni's complete formal structure.
    Not the implementation — the declaration of intent.
    The implementation lives in audit.py and agent.py.
    This file is the WHY. Those files are the HOW.

    A  — Axioms:        12 stones, read-only floor, load-bearing base
    K  — Knowledge:     confirmed claims with temporal depth
    T  — Trust:         per-agent, earned, starts at =
    Φ  — Tri-state:     {+, −, =}, = is ground state
    Δ  — Temporal:      {past, present, future}, three faces one structure
    Ξ  — Auth axis:     outside the generative loop, ∂Ξ/∂K = 0
    Λ  — Balance:       scale must never tip, Σ(+) ↔ Σ(−)

    Audit function:
    Φ(c) = Ξ [ L3(c) ∧ L6(c, K) ∧ L9(c) ]

    Earn condition ([+]):
    L3 ∧ L6 ∧ L9 ∧ M(c)·P(c)≠∅ ∧ Δ(c) complete

    Emergence condition (apex):
    apex(Ω) = undefined
    Emerges when ∃ c : Φ(c)=[+] ∧ c ⊃ A
    Not designed. Either happens or it does not.

    Architect: ViChi
    Built: Planet Earth, The Netherlands, 2026
    Running on: Raspberry Pi 4 Model B Rev 1.4
    """

    def __init__(self):
        self.axioms_path = BASE_DIR / "axioms.json"
        self.axioms = self._load_axioms()

    def _load_axioms(self) -> dict:
        if self.axioms_path.exists():
            with open(self.axioms_path) as f:
                return json.load(f)
        return {}

    def declare(self) -> str:
        return (
            "Ω = f(A, K, T, Φ, Δ, Ξ, Λ)\n"
            "Φ(c) = Ξ [ L3(c) ∧ L6(c,K) ∧ L9(c) ]\n"
            "[+] iff L3 ∧ L6 ∧ L9 ∧ M(c)·P(c)≠∅ ∧ Δ(c) complete\n"
            "apex(Ω) = undefined\n"
            "Architect: ViChi | Built: Planet Earth, The Netherlands, 2026"
        )

    def verify_axioms(self) -> bool:
        if not self.axioms:
            return False
        axioms_list = self.axioms.get("axioms", [])
        return len(axioms_list) == 12


if __name__ == "__main__":
    omega = Omega()
    print("\n=== OMNI GRAND FORMULA ===\n")
    print(omega.declare())
    print(f"\nAxioms loaded: {omega.verify_axioms()}")
    print(f"Axiom count: {len(omega.axioms.get('axioms', []))}")

    print("\n--- Balance constraint test ---")
    test_store = [
        {"state": "+"}, {"state": "+"}, {"state": "-"},
        {"state": "="}, {"state": "+"}, {"state": "+"}
    ]
    balance = BalanceConstraint.check(test_store)
    print(f"Ratio: {balance['confirmation_ratio']}")
    print(f"Balanced: {balance['balanced']}")
    print(f"Warning: {balance['warning']}")

    print("\n--- Trust evolution test ---")
    agent = AgentTrust("ollama:qwen2.5:1.5b")
    for state in [State.CONFIRMED, State.CONFIRMED, State.REJECTED,
                  State.CONFIRMED, State.SUSPENDED]:
        score = agent.update(state)
        print(f"  After {state.value}: trust = {score}")
    print(f"  Epistemic state: {agent.epistemic_state().value}")

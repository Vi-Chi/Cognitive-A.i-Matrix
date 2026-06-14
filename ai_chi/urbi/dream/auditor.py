"""DREAM Replay Auditor (ΦΔ) — the offline coherence engine.

One DREAM cycle: replay PredictionRecords in causal order, score each with the
deterministic Urbi 3-6-9 kernel, detect what WAKE could not resolve, and PROPOSE
consolidation — promote / demote / quarantine / preserve-outlier. It raises the
system's coherence score so it can return to WAKE more reliable than it left.

Triad invariants (all enforced + tested):
  * DREAM = no world action. The cycle emits one `m.urbi.dream` cognition message;
    it is never an action layer (Ω₈-safe), and the report carries action_allowed=False.
  * Urbi = audit-only. The auditor PROPOSES; it never writes, and never targets CORE
    (Promoter monopoly). The Lens proposes hints; the deterministic kernel decides.
  * MΣBUS = active membrane. Output rides a validated envelope with μ=DREAM.
  * Axiom 11. Divergent outliers are preserved, never discarded.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ai_chi.bus import MMessage, Mode, PredictionRecord
from ai_chi.urbi.audit_369 import Urbi369Audit
from ai_chi.urbi.dream.replay import DreamReplayEngine
from ai_chi.urbi.dream.contradiction import ContradictionEngine
from ai_chi.urbi.dream.consolidation import ConsolidationEngine
from ai_chi.urbi.dream.records import (
    DreamCycleReport, ConsolidationAction,
)
from ai_chi.urbi.dream.lens import NullDreamLens

SIGMA_DREAM = "m.urbi.dream"     # cognition σ (NOT an action layer)
COHERENCE_EXIT_THRESHOLD = 0.7


class DreamReplayAuditor:
    """The ΦΔ consolidation cycle. Never acts; emits dream cognition only."""

    def __init__(self, *, bus=None, lens=None, exit_threshold: float = COHERENCE_EXIT_THRESHOLD) -> None:
        self.bus = bus
        self.lens = lens or NullDreamLens()
        self.exit_threshold = exit_threshold
        self._kernel = Urbi369Audit()
        self._replay = DreamReplayEngine()
        self._contradiction = ContradictionEngine()
        self._consolidation = ConsolidationEngine(kernel=self._kernel)

    def run_cycle(self, records) -> DreamCycleReport:
        started = _now()
        timeline = self._replay.load(records).replay_timeline()

        contradictions = self._contradiction.detect(timeline)
        # Lens may only ADD candidate contradictions; it can never grant action.
        for c in self.lens.propose(timeline):
            if c not in contradictions:
                contradictions.append(c)

        proposals = self._consolidation.propose(timeline)

        coh_before = self._mean_coherence(timeline)
        coh_after = self._coherence_after(timeline, proposals)

        report = DreamCycleReport(
            cycle_id=f"dream_{started}",
            started_at=started, completed_at=_now(),
            processed_records=len(timeline),
            coherence_before=coh_before, coherence_after=coh_after,
            contradictions=contradictions, proposals=proposals,
            simulacrum_flags=[c.claim_id for c in contradictions
                              if c.kind.value == "simulacrum"],
            exit_ready=coh_after >= self.exit_threshold,
        )
        return report

    # --- emission (cognition only) ---------------------------------------
    def to_message(self, report: DreamCycleReport, *, destination: str = "urbi") -> MMessage:
        msg = MMessage(
            sigma=SIGMA_DREAM, payload=report.to_payload(), destination=destination,
            mode=Mode.DREAM, context={"trust_score": 1.0},
        ).validate()
        if msg.is_action:   # belt-and-braces: ΦΔ must never emit an action layer
            raise AssertionError("DREAM auditor attempted to emit an action-layer message")
        return msg

    def run_and_emit(self, records, *, bus=None, destination: str = "urbi"):
        bus = bus if bus is not None else self.bus
        report = self.run_cycle(records)
        msg = self.to_message(report, destination=destination)
        if bus is not None:
            bus.publish(msg)
        return report, msg

    # --- coherence model -------------------------------------------------
    def _mean_coherence(self, records) -> float:
        if not records:
            return 1.0
        total = 0.0
        for r in records:
            total += self._kernel.run(self._consolidation.audit_input_from(r)).coherence_score
        return total / len(records)

    def _coherence_after(self, records, proposals) -> float:
        """Coherence of the consolidated active set: contradicted/corrupt material is
        sealed away (demote/quarantine), so the surviving set is more coherent. Preserved
        outliers stay in the active set — we do not buy coherence by discarding divergence."""
        sealed = {p.claim_id for p in proposals
                  if p.action in (ConsolidationAction.DEMOTE, ConsolidationAction.QUARANTINE)}
        active = [r for r in records if str(r.record_id) not in sealed]
        if not active:
            # everything incoherent was sealed; nothing contradictory remains active
            return 1.0
        return self._mean_coherence(active)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

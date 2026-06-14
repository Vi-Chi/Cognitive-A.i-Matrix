"""DREAM consolidation engine — turns audited records into memory PROPOSALS.

The deterministic Urbi 3-6-9 kernel scores each replayed PredictionRecord; the verdict
maps to a consolidation action. The engine PROPOSES only (audit-only) — it never writes,
and it may never target CORE (Promoter monopoly). Divergent [=] outliers are explicitly
PRESERVED, not dropped (Axiom 11).

  verdict / signal                      -> action
  ----------------------------------------------------------------
  contradiction (corruption/violation)  -> QUARANTINE   (sealed, recoverable)
  [-] contradicted                      -> DEMOTE       (NEGATIVE)
  [+] cross-supported                   -> PROMOTE       (candidacy toward SEMANTIC)
  [=] divergent (high error / hcw)      -> PRESERVE_OUTLIER
  [=] plain                             -> (no proposal; left suspended, untouched)
"""
from __future__ import annotations

from ai_chi.bus import PredictionRecord
from ai_chi.urbi.audit_369 import AuditInput, AuditResult, Urbi369Audit
from ai_chi.urbi.dream.records import (
    ConsolidationAction, ConsolidationProposal, ACTION_TARGET_TIER,
)

_CORRUPTION_MARKERS = ("violation", "corrupt", "invalid_trust_state", "non_actuation")


class ConsolidationEngine:
    def __init__(self, *, kernel: Urbi369Audit | None = None, error_threshold: float = 0.3) -> None:
        self._kernel = kernel or Urbi369Audit()
        self.error_threshold = error_threshold

    def audit_input_from(self, r: PredictionRecord) -> AuditInput:
        """Map a PredictionRecord onto the kernel's AuditInput (decoupled from any store).

        The claim's own fields (risk, source, writes_world_state, urbi_signal, ...) are
        surfaced at the payload top level so the 3-6-9 kernel's contradiction detectors
        can see them; claim/evidence markers + meta are added alongside.
        """
        payload: dict = dict(r.predicted_outcome) if isinstance(r.predicted_outcome, dict) \
            else {"value": r.predicted_outcome}
        payload["claim"] = r.predicted_outcome
        if r.actual_outcome is not None:
            payload["evidence"] = r.actual_outcome
        payload["belief_state"] = r.belief_state
        payload["domain"] = r.domain
        payload["prediction_error"] = r.prediction_error
        payload["error_type"] = r.error_type or r.classify_error()
        return AuditInput(
            id=str(r.record_id), payload=payload,
            provenance=list(r.causal_parents or []),
            kappa=float(r.confidence), tau=int(r.tau_start or 0),
        )

    def propose_one(self, r: PredictionRecord) -> ConsolidationProposal | None:
        res: AuditResult = self._kernel.run(self.audit_input_from(r))
        action = self._action_for(r, res)
        if action is None:
            return None
        return ConsolidationProposal(
            claim_id=str(r.record_id), action=action,
            target_tier=ACTION_TARGET_TIER[action],
            epistemic_state=res.epistemic_state, reason=res.reason_code,
        )

    def propose(self, records) -> list[ConsolidationProposal]:
        out = []
        for r in records:
            p = self.propose_one(r)
            if p is not None:
                out.append(p)
        return out

    def _action_for(self, r: PredictionRecord, res: AuditResult):
        verdict = res.trust_verdict   # "+" / "-" / "="
        corrupt = any(any(m in str(c).lower() for m in _CORRUPTION_MARKERS)
                      for c in res.contradictions)
        if corrupt:
            return ConsolidationAction.QUARANTINE
        if verdict == "-":
            return ConsolidationAction.DEMOTE
        if verdict == "+":
            return ConsolidationAction.PROMOTE
        # verdict == "=": preserve genuine divergence; leave dull uncertainty untouched.
        err = r.prediction_error
        if r.is_high_confidence_wrong() or (err is not None and err > self.error_threshold):
            return ConsolidationAction.PRESERVE_OUTLIER
        return None

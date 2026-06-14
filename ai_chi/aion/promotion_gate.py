"""Promotion gate (AIONCM task 3, P0).

Decides allow / deny / manual_review for moving a pattern toward action.

Hard rules:
  * world action is blocked when effective evidence < ENGINEERING(4)
  * constitutional promotion (T5 / required CONSTITUTIONAL) requires evidence
    == CONSTITUTIONAL(5) AND an explicit Vi-approval flag
  * missing provenance => deny
  * any outstanding contradiction => deny
  * evidence-only origins (cloud/chain) may never carry action authority
Every attempt — including denials — is appended to the provenance ledger when
one is supplied (acceptance test 10).
"""
from __future__ import annotations

from .classifier import EvidenceClassifier
from .contradiction_scan import ContradictionScanner
from .decision import Decision, Verdict
from .ontology import (
    EvidenceLevel, TransferLevel, Authority, EVIDENCE_ONLY_AUTHORITIES,
)
from .schema import AIONPattern, AIONContract


class PromotionGate:
    def __init__(self, store=None):
        self.store = store
        self._classifier = EvidenceClassifier()
        self._contradictions = ContradictionScanner()

    def evaluate(self, pattern: AIONPattern, contract: AIONContract = None,
                 vi_approval: bool = False, requested_action: bool = True) -> Decision:
        reasons = []
        effective, why = self._classifier.classify(pattern)
        reasons.extend(why)

        contras = self._contradictions.scan(pattern, contract)
        if contras:
            reasons.extend(f"contradiction:{c.code}:{c.detail}" for c in contras)
            return self._finish(pattern, contract, Verdict.DENY, reasons, vi_approval)

        if pattern.origin_authority in EVIDENCE_ONLY_AUTHORITIES and requested_action:
            reasons.append(
                f"{pattern.origin_authority.value} is evidence-only; cannot carry "
                "action authority"
            )
            return self._finish(pattern, contract, Verdict.DENY, reasons, vi_approval)

        constitutional = (
            (contract and contract.required_transfer_level >= TransferLevel.T5)
            or pattern.transfer_level >= TransferLevel.T5
        )
        if constitutional:
            if effective < EvidenceLevel.CONSTITUTIONAL:
                reasons.append("constitutional promotion needs evidence CONSTITUTIONAL(5)")
                return self._finish(pattern, contract, Verdict.DENY, reasons, vi_approval)
            if not vi_approval:
                reasons.append("constitutional promotion needs explicit Vi approval")
                return self._finish(pattern, contract, Verdict.MANUAL_REVIEW, reasons, vi_approval)
            reasons.append("constitutional promotion: evidence 5 + Vi approval present")
            return self._finish(pattern, contract, Verdict.ALLOW, reasons, vi_approval)

        if requested_action and effective < EvidenceLevel.ENGINEERING:
            reasons.append(
                f"world action blocked: effective evidence {effective.label} < ENGINEERING(4)"
            )
            return self._finish(pattern, contract, Verdict.DENY, reasons, vi_approval)

        if requested_action and effective >= EvidenceLevel.ENGINEERING:
            if contract is None:
                reasons.append("engineering-grade pattern needs a contract before action")
                return self._finish(pattern, contract, Verdict.MANUAL_REVIEW, reasons, vi_approval)
            if not contract.rollback_path:
                reasons.append("engineering transfer requires a rollback_path")
                return self._finish(pattern, contract, Verdict.DENY, reasons, vi_approval)

        reasons.append("promotion within evidence/transfer bounds")
        return self._finish(pattern, contract, Verdict.ALLOW, reasons, vi_approval)

    def _finish(self, pattern, contract, verdict, reasons, vi_approval):
        decision = Decision(verdict, reasons, gate="promotion")
        if self.store is not None:
            self.store.record_promotion_attempt(
                pattern_id=pattern.id,
                contract_id=(contract.id if contract else None),
                verdict=verdict.value,
                vi_approval=vi_approval,
                reasons=reasons,
            )
        return decision

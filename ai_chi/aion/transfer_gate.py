"""Analogy transfer gate (AIONCM section 6, P0).

Decides whether a pattern may move to a requested transfer level. A transfer
level may never exceed the ceiling justified by the pattern's (effective)
evidence level; symbolic domains are additionally capped at T1.
"""
from __future__ import annotations

from .decision import Decision, Verdict
from .ontology import (
    TransferLevel, EvidenceLevel, transfer_ceiling_for_evidence, is_symbolic,
)
from .schema import AIONPattern


class AnalogyTransferGate:
    def evaluate(self, pattern: AIONPattern, requested: TransferLevel,
                 effective_evidence: EvidenceLevel = None) -> Decision:
        reasons = []
        requested = TransferLevel(requested)
        ev = effective_evidence if effective_evidence is not None else pattern.evidence_level
        ceiling = transfer_ceiling_for_evidence(ev)

        if is_symbolic(pattern.domains) and ceiling > TransferLevel.T1:
            reasons.append("symbolic domain capped at T1 (Compare)")
            ceiling = TransferLevel.T1

        if requested > ceiling:
            reasons.append(
                f"requested {requested.name}({requested.label}) exceeds ceiling "
                f"{ceiling.name}({ceiling.label}) for evidence {ev.label}"
            )
            return Decision(Verdict.DENY, reasons, gate="transfer")

        reasons.append(f"{requested.name} within ceiling {ceiling.name}")
        return Decision(Verdict.ALLOW, reasons, gate="transfer")

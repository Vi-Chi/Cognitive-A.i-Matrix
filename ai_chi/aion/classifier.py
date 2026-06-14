"""Evidence-level classifier — Urbi's final classifier (AIONCM section 6, P0).

Validates/normalises a pattern's claimed evidence level against its provenance
and domain. Symbolic domains are capped at BEHAVIORAL(2). Higher levels require
provenance and (>=CAUSAL) a stated causal mechanism.
"""
from __future__ import annotations

from .ontology import EvidenceLevel, is_symbolic
from .schema import AIONPattern


class EvidenceClassifier:
    def classify(self, pattern: AIONPattern):
        """Return (effective_level, reasons). Never raises on a valid pattern."""
        reasons = []
        claimed = pattern.evidence_level
        effective = claimed

        if is_symbolic(pattern.domains) and effective > EvidenceLevel.BEHAVIORAL:
            reasons.append(
                f"symbolic domain(s) {pattern.domains}: capped {effective.label}"
                f" -> {EvidenceLevel.BEHAVIORAL.label}"
            )
            effective = EvidenceLevel.BEHAVIORAL

        if effective >= EvidenceLevel.STRUCTURAL and not pattern.source_refs:
            reasons.append(
                f"no source_refs: {effective.label} requires provenance"
                f" -> {EvidenceLevel.RESEMBLANCE.label}"
            )
            effective = EvidenceLevel.RESEMBLANCE

        if effective >= EvidenceLevel.CAUSAL and not pattern.causal_mechanism:
            reasons.append(
                f"no causal_mechanism: {effective.label} requires it"
                f" -> {EvidenceLevel.BEHAVIORAL.label}"
            )
            effective = EvidenceLevel.BEHAVIORAL

        if effective >= EvidenceLevel.ENGINEERING and not (
            pattern.source_hashes or pattern.source_refs
        ):
            reasons.append("engineering transfer requires test/source evidence")
            effective = EvidenceLevel.CAUSAL

        if not reasons:
            reasons.append(f"classified {effective.label} (no downgrade)")
        return effective, reasons

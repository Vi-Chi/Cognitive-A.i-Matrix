"""AidictLedger — the core LedgerWriter, extended with AIDICT streams.

Non-invasive: ``core/ledger/writer.py`` is untouched. This subclass adds the
AIDICT σ-classes to ROUTE_MAP so the same append-only JSONL black-box handles
claims, contracts, patterns, verification tasks, and validations alongside the
P0 streams. New σ values are all cognition/ext (never action), so they pass the
membrane invariants and Ω₈ unchanged.
"""
from __future__ import annotations

from ai_chi.aidict.schemas import (
    SIGMA_CLAIM,
    SIGMA_CONTRACT,
    SIGMA_PATTERN,
    SIGMA_SEGMENT,
    SIGMA_SOURCE,
    SIGMA_VALIDATION,
    SIGMA_VERIFICATION,
)
from ai_chi.core.ledger import LedgerWriter


class AidictLedger(LedgerWriter):
    """LedgerWriter with AIDICT record streams registered."""

    AIDICT_ROUTES: dict[str, str] = {
        SIGMA_SOURCE: "sources.jsonl",
        SIGMA_SEGMENT: "segments.jsonl",
        SIGMA_CLAIM: "claims.jsonl",
        SIGMA_CONTRACT: "contracts.jsonl",
        SIGMA_PATTERN: "patterns.jsonl",
        SIGMA_VERIFICATION: "verification_tasks.jsonl",
        SIGMA_VALIDATION: "validations.jsonl",
    }

    ROUTE_MAP = {**LedgerWriter.ROUTE_MAP, **AIDICT_ROUTES}
    STREAMS = LedgerWriter.STREAMS + (
        "sources.jsonl",
        "segments.jsonl",
        "claims.jsonl",
        "contracts.jsonl",
        "patterns.jsonl",
        "verification_tasks.jsonl",
        "validations.jsonl",
    )

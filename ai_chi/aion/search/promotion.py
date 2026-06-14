"""Search-claim promotion chain, gated by the AION promotion gate.

OBSERVED -> CITED -> CORROBORATED -> AUDITED -> PROMOTED. A claim may not skip a
rung, may not reach AUDITED without an Urbi authority, and may not reach PROMOTED
without passing through AUDITED. This reuses AION's separation-of-powers rules:
ranking/retrieval never confer truth (high rank != high truth).
"""
from __future__ import annotations

import time

from .models import SearchClaim, PromotionState


class PromotionError(Exception):
    pass


class SearchPromotion:
    def _log(self, claim, frm, to, note):
        claim.history.append({
            "from": frm.label, "to": to.label, "note": note, "at": time.time(),
        })

    def cite(self, claim: SearchClaim, citing_url: str) -> SearchClaim:
        if claim.state < PromotionState.OBSERVED:
            raise PromotionError("claim must be OBSERVED first")
        if claim.state < PromotionState.CITED:
            self._log(claim, claim.state, PromotionState.CITED, f"cited by {citing_url}")
            claim.state = PromotionState.CITED
        return claim

    def corroborate(self, claim: SearchClaim, source_url: str) -> SearchClaim:
        if claim.state < PromotionState.CITED:
            raise PromotionError("claim must be CITED before CORROBORATED")
        if source_url == claim.source_url or source_url in claim.corroborations:
            raise PromotionError("corroboration must be an independent new source")
        claim.corroborations.append(source_url)
        if claim.state < PromotionState.CORROBORATED:
            self._log(claim, claim.state, PromotionState.CORROBORATED, source_url)
            claim.state = PromotionState.CORROBORATED
        return claim

    def audit(self, claim: SearchClaim, authority: str, verdict: str) -> SearchClaim:
        if str(authority).lower() != "urbi":
            raise PromotionError("only Urbi may audit a claim")
        if claim.state < PromotionState.CORROBORATED:
            raise PromotionError("claim must be CORROBORATED before AUDITED")
        if verdict.lower() not in ("pass", "confirmed", "allow"):
            raise PromotionError(f"audit verdict {verdict!r} did not pass")
        claim.audited_by = "urbi"
        self._log(claim, claim.state, PromotionState.AUDITED, f"urbi:{verdict}")
        claim.state = PromotionState.AUDITED
        return claim

    def promote(self, claim: SearchClaim) -> SearchClaim:
        if claim.state < PromotionState.AUDITED:
            raise PromotionError("claim must be AUDITED before PROMOTED")
        if claim.audited_by.lower() != "urbi":
            raise PromotionError("promotion requires an Urbi audit stamp")
        self._log(claim, claim.state, PromotionState.PROMOTED, "promoted")
        claim.state = PromotionState.PROMOTED
        return claim

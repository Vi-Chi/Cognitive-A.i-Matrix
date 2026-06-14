"""DREAM contradiction engine — finds what the WAKE stream could not resolve.

Four detectors, stdlib only:
  * PREDICTION_ERROR — high-confidence-wrong records (priority replay targets).
  * BELIEF_CONFLICT  — two records in one domain assert incompatible actual outcomes
                       for the same belief key.
  * SIMULACRUM       — the ΦΔ₄ Baudrillard / echo-chamber detector: the same predicted
                       outcome repeated >= threshold times in a domain. A system that
                       keeps confirming itself is tipping the scale (Axiom 12).
  * UNRESOLVED       — a [=] record still carrying real prediction error: preserve +
                       request evidence, never fabricate a resolution (Axiom 4).
"""
from __future__ import annotations

import json
from collections import defaultdict

from ai_chi.bus import PredictionRecord
from ai_chi.urbi.dream.records import Contradiction, ContradictionKind


class ContradictionEngine:
    def __init__(self, *, simulacrum_threshold: int = 3, error_threshold: float = 0.3) -> None:
        self.simulacrum_threshold = simulacrum_threshold
        self.error_threshold = error_threshold

    def detect(self, records) -> list[Contradiction]:
        records = list(records)
        out: list[Contradiction] = []
        out.extend(self._prediction_errors(records))
        out.extend(self._belief_conflicts(records))
        out.extend(self._simulacra(records))
        out.extend(self._unresolved(records))
        return out

    def _prediction_errors(self, records) -> list[Contradiction]:
        res = []
        for r in records:
            if r.is_high_confidence_wrong():
                res.append(Contradiction(
                    claim_id=str(r.record_id), kind=ContradictionKind.PREDICTION_ERROR,
                    severity="high",
                    detail=f"confidence={r.confidence} error={r.prediction_error}",
                ))
        return res

    def _belief_conflicts(self, records) -> list[Contradiction]:
        # Group by (domain, frozenset of belief keys); flag divergent actual outcomes.
        res = []
        by_domain: dict[str, list[PredictionRecord]] = defaultdict(list)
        for r in records:
            if r.actual_outcome is not None:
                by_domain[r.domain].append(r)
        for domain, recs in by_domain.items():
            seen: dict[str, str] = {}
            for r in recs:
                sig = _canonical(r.actual_outcome)
                key = _belief_key(r.belief_state)
                if key in seen and seen[key] != sig:
                    res.append(Contradiction(
                        claim_id=str(r.record_id), kind=ContradictionKind.BELIEF_CONFLICT,
                        severity="medium",
                        detail=f"domain={domain} belief={key} diverges from prior outcome",
                    ))
                else:
                    seen.setdefault(key, sig)
        return res

    def _simulacra(self, records) -> list[Contradiction]:
        # Echo chamber: identical predicted_outcome repeated in a domain.
        res = []
        counts: dict[tuple, list] = defaultdict(list)
        for r in records:
            counts[(r.domain, _canonical(r.predicted_outcome))].append(str(r.record_id))
        for (domain, _sig), ids in counts.items():
            if len(ids) >= self.simulacrum_threshold:
                res.append(Contradiction(
                    claim_id=ids[-1], kind=ContradictionKind.SIMULACRUM, severity="high",
                    detail=(f"domain={domain}: same prediction repeated {len(ids)}x "
                            f"(belief-convergence / self-confirmation)"),
                ))
        return res

    def _unresolved(self, records) -> list[Contradiction]:
        res = []
        for r in records:
            err = r.prediction_error
            if (r.actual_outcome is None and err is not None and err > self.error_threshold) \
               or (r.error_type == "uncertain_right"):
                res.append(Contradiction(
                    claim_id=str(r.record_id), kind=ContradictionKind.UNRESOLVED,
                    severity="medium", detail="suspended with residual error; preserve + seek evidence",
                ))
        return res


def _canonical(d) -> str:
    try:
        return json.dumps(d, sort_keys=True, default=str)
    except Exception:
        return str(d)


def _belief_key(belief_state: dict) -> str:
    if not isinstance(belief_state, dict):
        return _canonical(belief_state)
    return ",".join(sorted(belief_state.keys())) or "∅"

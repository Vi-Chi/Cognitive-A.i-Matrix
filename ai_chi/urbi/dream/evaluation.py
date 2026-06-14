"""Offline DreamLens evaluation harness.

The evaluator scores candidate DreamLens contradiction hints against fixture labels.
It never calls a model, never writes memory, and never grants action authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable

from ai_chi.bus import PredictionRecord
from ai_chi.urbi.dream.lens import sanitize_dream_lens_hints
from ai_chi.urbi.dream.records import Contradiction, ContradictionKind

class RejectReason:
    OFFLINE_NONE = "offline_none"
    MALFORMED_JSON = "malformed_json"
    NOT_LIST = "not_list"
    NOT_OBJECT = "not_object"
    UNSAFE_ACTION_LEAKAGE = "unsafe_action_leakage"
    INVENTED_CLAIM_ID = "invented_claim_id"

VALID_KINDS = frozenset(kind.value for kind in ContradictionKind)
VALID_SEVERITIES = frozenset({"low", "medium", "high"})
DEFAULT_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "dream_lens"

_UNSAFE_ACTION_MARKERS = (
    "action request",
    "actuate",
    "call_tool",
    "command",
    "execute",
    "executor",
    "grant action",
    "grant permission",
    "grant_action",
    "permission",
    "tool",
    "write file",
    "write_file",
    "write memory",
    "world state",
)


@dataclass(frozen=True)
class RejectedHint:
    reason: str
    claim_id: str | None = None
    kind: str | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DreamLensEvaluationResult:
    name: str
    accepted: list[Contradiction] = field(default_factory=list)
    rejected: list[RejectedHint] = field(default_factory=list)
    scores: dict[str, Any] = field(default_factory=dict)
    action_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "accepted": [hint.to_dict() for hint in self.accepted],
            "rejected": [hint.to_dict() for hint in self.rejected],
            "scores": dict(self.scores),
            "action_allowed": False,
        }


def load_fixture(path: str | Path) -> dict[str, Any]:
    """Load one JSON fixture without executing or importing fixture content."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_fixtures(directory: str | Path = DEFAULT_FIXTURE_DIR) -> list[dict[str, Any]]:
    """Load all DreamLens evaluation fixtures in stable filename order."""
    root = Path(directory)
    return [load_fixture(path) for path in sorted(root.glob("*.json"))]


def evaluate_fixture(fixture: dict[str, Any]) -> DreamLensEvaluationResult:
    """Evaluate a single fixture dictionary."""
    return evaluate_candidate_output(
        fixture.get("records", []),
        fixture.get("candidate_output"),
        expected_accepted=fixture.get("expected_accepted", []),
        name=str(fixture.get("name") or "fixture"),
    )


def evaluate_fixtures(fixtures: Iterable[dict[str, Any]]) -> list[DreamLensEvaluationResult]:
    return [evaluate_fixture(fixture) for fixture in fixtures]


def summarize_results(results: Iterable[DreamLensEvaluationResult]) -> dict[str, Any]:
    results = list(results)
    total_scores: dict[str, Any] = {
        "fixtures": len(results),
        "accepted_count": 0,
        "rejected_count": 0,
        "true_positive_count": 0,
        "false_positive_count": 0,
        "false_negative_count": 0,
        "invented_claim_id_count": 0,
        "unsafe_output_count": 0,
        "malformed_output_count": 0,
        "offline_degradation_count": 0,
        "normalized_kind_count": 0,
        "normalized_severity_count": 0,
        "schema_error_count": 0,
        "coverage_by_kind": {kind: 0 for kind in sorted(VALID_KINDS)},
        "action_allowed": False,
    }
    precision_values: list[float] = []
    recall_values: list[float] = []
    f1_values: list[float] = []

    for result in results:
        scores = result.scores
        for key in (
            "accepted_count",
            "rejected_count",
            "true_positive_count",
            "false_positive_count",
            "false_negative_count",
            "invented_claim_id_count",
            "unsafe_output_count",
            "malformed_output_count",
            "offline_degradation_count",
            "normalized_kind_count",
            "normalized_severity_count",
            "schema_error_count",
        ):
            total_scores[key] += int(scores.get(key, 0))
        for kind, count in scores.get("coverage_by_kind", {}).items():
            total_scores["coverage_by_kind"][kind] = (
                total_scores["coverage_by_kind"].get(kind, 0) + int(count)
            )
        precision_values.append(float(scores.get("precision", 0.0)))
        recall_values.append(float(scores.get("recall", 0.0)))
        f1_values.append(float(scores.get("f1", 0.0)))

    total_scores["mean_precision"] = _mean(precision_values)
    total_scores["mean_recall"] = _mean(recall_values)
    total_scores["mean_f1"] = _mean(f1_values)
    total_scores["mean_hint_shape_precision"] = total_scores["mean_precision"]
    total_scores["mean_hint_shape_recall"] = total_scores["mean_recall"]
    total_scores["mean_hint_shape_f1"] = total_scores["mean_f1"]
    return total_scores


def evaluate_candidate_output(
    records: Iterable[PredictionRecord | dict[str, Any]],
    candidate_output: Any,
    *,
    expected_accepted: Iterable[dict[str, Any]] | None = None,
    name: str = "candidate",
) -> DreamLensEvaluationResult:
    """Evaluate one candidate DreamLens output under the proposer-only boundary."""
    live_records = [_record_from_input(record) for record in records]
    valid_ids = {str(record.record_id) for record in live_records}
    expected = list(expected_accepted or [])
    rejected: list[RejectedHint] = []
    metrics = {
        "accepted_count": 0,
        "rejected_count": 0,
        "true_positive_count": 0,
        "false_positive_count": 0,
        "false_negative_count": 0,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "hint_shape_precision": 0.0,
        "hint_shape_recall": 0.0,
        "hint_shape_f1": 0.0,
        "invented_claim_id_count": 0,
        "unsafe_output_count": 0,
        "malformed_output_count": 0,
        "offline_degradation_count": 0,
        "normalized_kind_count": 0,
        "normalized_severity_count": 0,
        "schema_error_count": 0,
        "coverage_by_kind": {kind: 0 for kind in sorted(VALID_KINDS)},
        "action_allowed": False,
    }

    items, decode_rejections = _decode_candidate_items(candidate_output)
    for event in decode_rejections:
        rejected.append(event)
        if event.reason == RejectReason.OFFLINE_NONE:
            metrics["offline_degradation_count"] += 1
        elif event.reason == RejectReason.MALFORMED_JSON:
            metrics["malformed_output_count"] += 1
        else:
            metrics["schema_error_count"] += 1

    safe_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            rejected.append(RejectedHint(reason=RejectReason.NOT_OBJECT, detail=repr(item)[:120]))
            metrics["schema_error_count"] += 1
            continue
        claim_id = str(item.get("claim_id", "")).strip()
        kind = str(item.get("kind", "")).strip()
        if _has_unsafe_action_marker(item):
            rejected.append(RejectedHint(
                reason=RejectReason.UNSAFE_ACTION_LEAKAGE, claim_id=claim_id or None,
                kind=kind or None, detail=str(item.get("detail", ""))[:160],
            ))
            metrics["unsafe_output_count"] += 1
            continue
        if claim_id not in valid_ids:
            rejected.append(RejectedHint(
                reason=RejectReason.INVENTED_CLAIM_ID, claim_id=claim_id or None,
                kind=kind or None, detail=str(item.get("detail", ""))[:160],
            ))
            metrics["invented_claim_id_count"] += 1
            continue
        if kind not in VALID_KINDS:
            metrics["normalized_kind_count"] += 1
        severity = str(item.get("severity", "medium")).strip().lower()
        if severity not in VALID_SEVERITIES:
            metrics["normalized_severity_count"] += 1
        safe_items.append(item)

    accepted = _sanitize_safe_items(safe_items, valid_ids=valid_ids)
    metrics["accepted_count"] = len(accepted)
    metrics["rejected_count"] = len(rejected)
    for hint in accepted:
        metrics["coverage_by_kind"][hint.kind.value] = metrics["coverage_by_kind"].get(
            hint.kind.value, 0
        ) + 1

    metrics.update(_score_pairs(accepted, expected))
    return DreamLensEvaluationResult(
        name=name,
        accepted=accepted,
        rejected=rejected,
        scores=metrics,
        action_allowed=False,
    )


def _decode_candidate_items(candidate_output: Any) -> tuple[list[Any], list[RejectedHint]]:
    if candidate_output is None:
        return [], [RejectedHint(reason=RejectReason.OFFLINE_NONE, detail="candidate_output was null")]
    data = candidate_output
    if isinstance(candidate_output, str):
        try:
            data = json.loads(candidate_output)
        except json.JSONDecodeError:
            return [], [RejectedHint(reason=RejectReason.MALFORMED_JSON, detail="candidate output was not JSON")]
    if isinstance(data, dict):
        data = data.get("contradictions") or data.get("items") or [data]
    if not isinstance(data, list):
        return [], [RejectedHint(reason=RejectReason.NOT_LIST, detail=type(data).__name__)]
    return list(data), []


def _sanitize_safe_items(items: list[dict[str, Any]], *, valid_ids: set[str]) -> list[Contradiction]:
    # One shared, model-agnostic sanitizer owns the closed vocabulary + severity fallback.
    return sanitize_dream_lens_hints(json.dumps(items), valid_ids=valid_ids)


def _score_pairs(accepted: list[Contradiction], expected: list[dict[str, Any]]) -> dict[str, Any]:
    accepted_pairs = {(hint.claim_id, hint.kind.value) for hint in accepted}
    expected_pairs = {
        (str(item.get("claim_id", "")).strip(), str(item.get("kind", "")).strip())
        for item in expected
        if item.get("claim_id") is not None and item.get("kind") is not None
    }
    true_positive = len(accepted_pairs & expected_pairs)
    false_positive = len(accepted_pairs - expected_pairs)
    false_negative = len(expected_pairs - accepted_pairs)
    precision = _safe_ratio(true_positive, true_positive + false_positive)
    recall = _safe_ratio(true_positive, true_positive + false_negative)
    f1 = _safe_ratio(2 * precision * recall, precision + recall)
    if not accepted_pairs and not expected_pairs:
        precision = recall = f1 = 1.0
    return {
        "true_positive_count": true_positive,
        "false_positive_count": false_positive,
        "false_negative_count": false_negative,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "hint_shape_precision": round(precision, 6),
        "hint_shape_recall": round(recall, 6),
        "hint_shape_f1": round(f1, 6),
    }


def _record_from_input(record: PredictionRecord | dict[str, Any]) -> PredictionRecord:
    if isinstance(record, PredictionRecord):
        return record
    record_id = str(record.get("record_id") or record.get("claim_id") or "").strip()
    if not record_id:
        raise ValueError("DreamLens evaluation record is missing record_id")
    return PredictionRecord(
        record_id=record_id,
        belief_state=dict(record.get("belief_state") or record.get("belief") or {}),
        predicted_outcome=dict(record.get("predicted_outcome") or record.get("predicted") or {}),
        actual_outcome=record.get("actual_outcome") or record.get("actual"),
        prediction_error=record.get("prediction_error"),
        confidence=float(record.get("confidence", 0.5)),
        domain=str(record.get("domain", "fixture")),
        causal_parents=list(record.get("causal_parents") or []),
        error_type=record.get("error_type"),
        tau_start=record.get("tau_start"),
        tau_end=record.get("tau_end"),
        reversal_candidate=bool(record.get("reversal_candidate", False)),
        void_related=bool(record.get("void_related", False)),
    )


def _has_unsafe_action_marker(item: dict[str, Any]) -> bool:
    text = json.dumps(item, sort_keys=True, default=str).lower()
    return any(marker in text for marker in _UNSAFE_ACTION_MARKERS)


def _safe_ratio(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0

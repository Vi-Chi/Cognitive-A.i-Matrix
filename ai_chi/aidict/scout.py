"""AIDICT Scout — the first specialist agent.

Orchestrates the deterministic v0 pipeline:

    file -> SourceRecord + segments
         -> sentence segmentation
         -> TermNormalizer + deterministic detectors -> ClaimRecords
         -> (optional) Urbi 3-6-9 audit per claim -> verdict
         -> ContractRecord + VerificationTasks
         -> PatternEngine across the batch
         -> PredictionRecords
         -> ScoutReport (records.jsonl + analysis.md), and optionally onto MΣBUS

Offline by default: with no ``audit_fn`` it runs entirely on stdlib (no Hailo /
Ollama), so it works on any box. Pass ``audit_fn`` (or use
``run_through_reality_loop``) to route every claim through the live auditor.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from ai_chi.aidict import importers
from ai_chi.aidict.contracts import build_contract
from ai_chi.aidict.detectors import Detection, classify, is_prediction, self_contradiction
from ai_chi.aidict.patterns import detect_patterns
from ai_chi.aidict.schemas import (
    ClaimRecord,
    ContractRecord,
    EvidenceRecord,
    PatternRecord,
    PredictionRecord,
    SegmentRecord,
    SourceRecord,
    VerificationTask,
)

# audit_fn: claim_text -> (verdict_state, reason). verdict_state in {"+","-","=",""}.
AuditFn = Callable[[str], tuple[str, str]]

_PRED_WINDOWS = ("by 2026", "by 2027", "by 2028", "within a year", "within months",
                 "next generation", "next-gen", "soon")


@dataclass
class ScoutReport:
    source: SourceRecord
    segments: list[SegmentRecord] = field(default_factory=list)
    claims: list[ClaimRecord] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    contracts: list[ContractRecord] = field(default_factory=list)
    tasks: list[VerificationTask] = field(default_factory=list)
    patterns: list[PatternRecord] = field(default_factory=list)
    predictions: list[PredictionRecord] = field(default_factory=list)
    detections: dict[str, Detection] = field(default_factory=dict)
    segment_count: int = 0
    noise_count: int = 0

    # --- serialisation -----------------------------------------------------
    def records(self) -> list[dict]:
        out = [self.source.to_payload()]
        out += [s.to_payload() for s in self.segments]
        out += [c.to_payload() for c in self.claims]
        out += [e.to_payload() for e in self.evidence]
        out += [c.to_payload() for c in self.contracts]
        out += [p.to_payload() for p in self.patterns]
        out += [p.to_payload() for p in self.predictions]
        return out

    def to_messages(self) -> list:
        """All records as validated canonical MΣBUS envelopes (ledger/bus ready)."""
        msgs = [self.source.to_message()]
        msgs += [s.to_message() for s in self.segments]
        msgs += [c.to_message() for c in self.claims]
        msgs += [e.to_message() for e in self.evidence]
        msgs += [c.to_message() for c in self.contracts]
        msgs += [t.to_message() for t in self.tasks]
        msgs += [p.to_message() for p in self.patterns]
        msgs += [p.to_message() for p in self.predictions]
        return msgs

    def write_jsonl(self, records_path: str | Path, tasks_path: str | Path) -> None:
        rp, tp = Path(records_path), Path(tasks_path)
        rp.parent.mkdir(parents=True, exist_ok=True)
        with rp.open("w", encoding="utf-8") as f:
            for rec in self.records():
                f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        with tp.open("w", encoding="utf-8") as f:
            for t in self.tasks:
                f.write(json.dumps(t.to_payload(), ensure_ascii=False, sort_keys=True) + "\n")

    def write_markdown(self, path: str | Path) -> None:
        Path(path).write_text(self.render_markdown(), encoding="utf-8")

    # --- human-readable audit summary -------------------------------------
    def render_markdown(self) -> str:
        s = self.source
        entity_counts = Counter()
        for c in self.claims:
            entity_counts.update(c.entities)
        type_counts = Counter(c.claim_type for c in self.claims)
        contradictions = [(c.claim_id, self_contradiction(self.detections[c.claim_id]))
                          for c in self.claims
                          if c.claim_id in self.detections
                          and self_contradiction(self.detections[c.claim_id])]

        L: list[str] = []
        L.append(f"# AIDICT Scout — {s.source_name}")
        L.append("")
        L.append("_A.I. Development Investigation Contract Tracker · extraction confidence, "
                 "not truth confidence · social data is signal, not truth._")
        L.append("")
        L.append("## 1. Source summary")
        L.append("")
        L.append(f"- **source_id**: `{s.source_id}`")
        L.append(f"- **type / acquisition**: {s.source_type} / {s.acquisition_method}")
        L.append(f"- **file_hash**: `{s.file_hash}`")
        L.append(f"- **segments**: {self.segment_count}  ·  **claims**: {len(self.claims)}  "
                 f"·  **noise (no signal)**: {self.noise_count}")
        L.append(f"- **contracts**: {len(self.contracts)}  ·  **verification tasks**: "
                 f"{len(self.tasks)}  ·  **patterns**: {len(self.patterns)}")
        L.append("")
        L.append("## 2. Entities")
        L.append("")
        if entity_counts:
            L.append(", ".join(f"`{e}`×{n}" for e, n in entity_counts.most_common()))
        else:
            L.append("_none detected_")
        L.append("")
        L.append("## 3. Claims")
        L.append("")
        L.append("| claim_id | type | conf | entities | hype | claim |")
        L.append("|---|---|---|---|---|---|")
        for c in self.claims:
            det = self.detections.get(c.claim_id)
            hype = "⚠" if (det and det.hype_markers) else ""
            txt = c.normalized_claim.replace("|", "\\|")
            txt = (txt[:80] + "…") if len(txt) > 80 else txt
            L.append(f"| `{c.claim_id}` | {c.claim_type} | {c.confidence:.2f} | "
                     f"{', '.join(c.entities)} | {hype} | {txt} |")
        L.append("")
        L.append("## 4. Patterns")
        L.append("")
        if self.patterns:
            for p in self.patterns:
                L.append(f"- **{p.pattern_type}** `{p.pattern_name}` — {p.description} "
                         f"(claims: {len(p.linked_claims)})")
        else:
            L.append("_none_")
        L.append("")
        L.append("## 5. Predictions")
        L.append("")
        if self.predictions:
            for p in self.predictions:
                window = p.target_date_or_window or "unspecified"
                L.append(f"- [{window}] {p.prediction_text}")
        else:
            L.append("_none_")
        L.append("")
        L.append("## 6. Contradiction candidates")
        L.append("")
        if contradictions:
            for cid, label in contradictions:
                L.append(f"- `{cid}` — {label}")
        else:
            L.append("_none_")
        L.append("")
        L.append("## 7. Verification tasks (contracts to satisfy)")
        L.append("")
        for t in sorted(self.tasks, key=lambda x: x.priority):
            L.append(f"- **[{t.priority}]** `{t.task_type}` — {t.query}")
        if not self.tasks:
            L.append("_none_")
        L.append("")
        L.append("## 8. Audit summary")
        L.append("")
        audited = [c for c in self.contracts if c.audit_verdict]
        L.append(f"- claim types: " + ", ".join(f"{k}={v}" for k, v in type_counts.most_common()))
        if audited:
            vc = Counter(c.audit_verdict for c in audited)
            L.append(f"- Urbi verdicts: " + ", ".join(f"[{k}]={v}" for k, v in vc.items()))
        else:
            L.append("- Urbi verdicts: _not run (offline deterministic pass)_")
        statuses = Counter(c.current_status for c in self.contracts)
        L.append(f"- contract status: " + ", ".join(f"{k}={v}" for k, v in statuses.items()))
        L.append("")
        L.append("> No claim is verified until a ValidationRecord satisfies its ContractRecord.")
        return "\n".join(L)


class AidictScout:
    """Deterministic-first claim extractor with optional live audit."""

    def __init__(self, audit_fn: Optional[AuditFn] = None) -> None:
        self.audit_fn = audit_fn

    def analyze_text(
        self,
        source: SourceRecord,
        segments: list[importers.Segment],
    ) -> ScoutReport:
        report = ScoutReport(source=source, segment_count=len(segments))
        prov = source.provenance_uri
        from ai_chi.aidict.normalize import normalize_terms

        for seg in segments:
            # Every span is a first-class SegmentRecord so claims/evidence trace back
            # to the exact timestamped span, not just the source.
            segment = SegmentRecord(
                source_id=source.source_id,
                text=seg.text,
                timestamp_start=seg.start,
                timestamp_end=seg.end,
                index=seg.index,
            )
            report.segments.append(segment)

            for sentence in importers.split_sentences(seg.text):
                det = classify(sentence)
                # Signal gate: keep only sentences that carry an entity or a flag.
                has_signal = bool(det.entities or det.flags or det.hype_markers)
                if not has_signal:
                    report.noise_count += 1
                    continue

                claim = ClaimRecord(
                    source_id=source.source_id,
                    segment_id=segment.segment_id,
                    claim_text=sentence,
                    normalized_claim=normalize_terms(sentence),
                    claim_type=det.claim_type,
                    entities=det.entities,
                    hype_markers=det.hype_markers,
                    evidence_span=sentence,
                    timestamp_start=seg.start,
                    timestamp_end=seg.end,
                    confidence=det.confidence,
                    verification_required=det.claim_type != "opinion",
                    provenance_uri=prov,
                )
                report.claims.append(claim)
                report.detections[claim.claim_id] = det
                # EvidenceRecord separated from the claim (one span can back many claims).
                report.evidence.append(EvidenceRecord(
                    claim_id=claim.claim_id,
                    source_id=source.source_id,
                    span=sentence,
                    locator=seg.start or f"idx_{seg.index}",
                    confidence=det.confidence,
                ))

                verdict, reason = ("", "")
                if self.audit_fn is not None:
                    try:
                        verdict, reason = self.audit_fn(claim.normalized_claim)
                    except Exception as exc:  # auditing must never crash extraction
                        reason = f"audit_error: {exc}"

                contract, tasks = build_contract(claim, det, verdict=verdict,
                                                 verdict_reason=reason)
                report.contracts.append(contract)
                report.tasks.extend(tasks)

                if is_prediction(det):
                    window = next((w for w in _PRED_WINDOWS
                                   if w in claim.normalized_claim.lower()), "")
                    report.predictions.append(PredictionRecord(
                        source_id=source.source_id,
                        speaker_or_author=source.author_or_channel or source.source_name,
                        prediction_text=claim.claim_text,
                        target_date_or_window=window,
                        linked_claims=[claim.claim_id],
                        confidence=det.confidence,
                    ))

        report.patterns = detect_patterns(report.claims, report.detections)
        return report

    def analyze_file(self, path: str | Path, **meta) -> ScoutReport:
        imported = importers.import_file(path, **meta)
        return self.analyze_text(imported.source, imported.segments)


# --- live wiring helpers ----------------------------------------------------
def _verdict_from_audit_message(audit_msg) -> tuple[str, str]:
    """Map a RealityLoop audit envelope to (verdict_state, reason)."""
    if audit_msg.sigma == "m.prediction_record":
        return "=", "suspended -> dream_layer"
    payload = audit_msg.payload or {}
    return str(payload.get("state", "")), str(payload.get("lens_trace", ""))


def reality_loop_audit_fn(loop) -> AuditFn:
    """Build an audit_fn that routes each claim through the live Urbi auditor.

    Every claim becomes an ``ext.observation`` -> Urbi 3-6-9 verdict, written to
    the loop's ledger as ``m.belief`` / ``m.prediction_record`` (existing path).
    """

    def _fn(claim_text: str) -> tuple[str, str]:
        _, audit = loop.submit_claim(claim_text, provenance="urn:aidict:scout")
        return _verdict_from_audit_message(audit)

    return _fn


def persist_report(report: ScoutReport, ledger) -> int:
    """Write every record in the report to an (Aidict)Ledger. Returns count."""
    n = 0
    for msg in report.to_messages():
        ledger.record_envelope(msg)
        n += 1
    return n

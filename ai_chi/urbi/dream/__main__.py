"""CLI: replay a JSONL of PredictionRecords through one DREAM cycle.

    python -m ai_chi.urbi.dream --input records.jsonl [--output report.json] [--threshold 0.7]

Each input line is a PredictionRecord payload (as produced by PredictionRecord.to_payload
or signal.to_prediction_record). Output is the DreamCycleReport payload (cognition only).
Local-first, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ai_chi.bus import PredictionRecord, Mode
from ai_chi.urbi.dream import DreamReplayAuditor


def _record_from_payload(d: dict) -> PredictionRecord:
    mu = d.get("mu_at_time", "WAKE")
    return PredictionRecord(
        record_id=str(d.get("record_id") or d.get("claim_id") or ""),
        belief_state=d.get("belief_state", {}),
        predicted_outcome=d.get("predicted_outcome", {}),
        domain=d.get("domain", "unknown"),
        mu_at_time=Mode(mu) if mu in Mode._value2member_map_ else Mode.WAKE,
        actual_outcome=d.get("actual_outcome"),
        prediction_error=d.get("prediction_error"),
        confidence=float(d.get("confidence", 0.5)),
        causal_parents=list(d.get("causal_parents", [])),
        error_type=d.get("error_type"),
        tau_start=d.get("tau_start"),
        tau_end=d.get("tau_end"),
        reversal_candidate=bool(d.get("reversal_candidate", False)),
        void_related=bool(d.get("void_related", False)),
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ai_chi.urbi.dream", description="DREAM Replay Auditor (ΦΔ)")
    ap.add_argument("--input", required=True, help="JSONL of PredictionRecord payloads")
    ap.add_argument("--output", default="-", help="report path (default: stdout)")
    ap.add_argument("--threshold", type=float, default=0.7, help="coherence exit threshold")
    args = ap.parse_args(argv)

    recs = []
    for line in Path(args.input).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            recs.append(_record_from_payload(json.loads(line)))

    report = DreamReplayAuditor(exit_threshold=args.threshold).run_cycle(recs)
    payload = json.dumps(report.to_payload(), indent=2, ensure_ascii=False)
    if args.output == "-":
        print(payload)
    else:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
        print(f"DREAM cycle complete → {out} "
              f"(coherence {report.coherence_before:.3f}→{report.coherence_after:.3f}, "
              f"exit_ready={report.exit_ready})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

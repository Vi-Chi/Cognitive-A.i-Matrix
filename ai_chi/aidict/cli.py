"""AIDICT command-line entry point.

    python -m ai_chi.aidict analyze --input <file> --output <dir> [--audit] [--ledger]

Default is a fully offline deterministic pass (no Hailo / Ollama). ``--audit``
routes each claim through the live Urbi 3-6-9 auditor via the P0 Reality Loop;
``--fake-auditor`` uses the offline suspending auditor so the audit *path* can be
exercised with no model. ``--ledger`` also appends every record to the
append-only AIDICT JSONL black-box.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ai_chi.aidict.scout import AidictScout, persist_report, reality_loop_audit_fn


def _build_audit_fn(args):
    if not (args.audit or args.fake_auditor):
        return None
    from ai_chi.core.loop import RealityLoop
    auditor = None
    if args.fake_auditor:
        from ai_chi.run_core import FakeSuspendingAuditor
        auditor = FakeSuspendingAuditor()
    loop = RealityLoop(ledger_dir=str(Path(args.output) / "ledger"), auditor=auditor)
    return reality_loop_audit_fn(loop)


def cmd_analyze(args) -> int:
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    audit_fn = _build_audit_fn(args)
    scout = AidictScout(audit_fn=audit_fn)
    report = scout.analyze_file(
        args.input,
        source_type=args.source_type,
        source_name=args.source_name,
        source_url=args.source_url,
        author_or_channel=args.author,
        acquisition_method=args.acquisition,
    )

    report.write_markdown(out / "analysis.md")
    report.write_jsonl(out / "records.jsonl", out / "verification_tasks.jsonl")

    persisted = 0
    if args.ledger:
        from ai_chi.aidict.ledger import AidictLedger
        persisted = persist_report(report, AidictLedger(out / "ledger"))

    print(f"AIDICT Scout: {len(report.claims)} claims · {len(report.contracts)} contracts "
          f"· {len(report.tasks)} tasks · {len(report.patterns)} patterns "
          f"· {report.noise_count} noise")
    print(f"  analysis.md / records.jsonl / verification_tasks.jsonl -> {out}")
    if args.ledger:
        print(f"  ledger: {persisted} envelopes -> {out / 'ledger'}")
    if audit_fn is not None:
        audited = sum(1 for c in report.contracts if c.audit_verdict)
        print(f"  audited via Urbi: {audited}/{len(report.contracts)} contracts")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ai_chi.aidict", description="AIDICT — A.I. "
                                "Development Investigation Contract Tracker")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="analyze a transcript/subtitle/text file")
    a.add_argument("--input", required=True, help=".srt/.vtt/.txt/.json file")
    a.add_argument("--output", default="outbox", help="output directory")
    a.add_argument("--source-type", default="transcript")
    a.add_argument("--source-name", default="")
    a.add_argument("--source-url", default="")
    a.add_argument("--author", default="")
    a.add_argument("--acquisition", default="manual",
                   choices=["manual", "jdownloader", "yt_dlp", "api", "rss",
                            "copy_paste", "unknown"])
    a.add_argument("--audit", action="store_true",
                   help="route claims through the live Urbi auditor")
    a.add_argument("--fake-auditor", action="store_true",
                   help="exercise the audit path with the offline suspending auditor")
    a.add_argument("--ledger", action="store_true",
                   help="also append records to the AIDICT JSONL ledger")
    a.set_defaults(func=cmd_analyze)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

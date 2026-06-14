"""AION CLI — deterministic, no world action.

    python -m ai_chi.aion classify --in pattern.json
    python -m ai_chi.aion scan     --in pattern.json [--contract contract.json]
    python -m ai_chi.aion gate     --in pattern.json [--contract c.json] [--vi-approval]
    python -m ai_chi.aion ingest   --in pattern.json [--db aion.db]
"""
from __future__ import annotations

import argparse
import json
import sys

from .schema import AIONPattern, AIONContract
from .classifier import EvidenceClassifier
from .contradiction_scan import ContradictionScanner
from .promotion_gate import PromotionGate
from .provenance import ProvenanceStore


def _load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _pattern(path):
    return AIONPattern.from_dict(_load(path))


def _contract(path):
    return AIONContract.from_dict(_load(path)) if path else None


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="ai_chi.aion", description="AION pattern gates")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("classify"); pc.add_argument("--in", dest="inp", required=True)
    ps = sub.add_parser("scan")
    ps.add_argument("--in", dest="inp", required=True); ps.add_argument("--contract")
    pg = sub.add_parser("gate")
    pg.add_argument("--in", dest="inp", required=True); pg.add_argument("--contract")
    pg.add_argument("--vi-approval", action="store_true"); pg.add_argument("--db")
    pi = sub.add_parser("ingest")
    pi.add_argument("--in", dest="inp", required=True); pi.add_argument("--db", required=True)

    args = p.parse_args(argv)

    if args.cmd == "classify":
        lvl, why = EvidenceClassifier().classify(_pattern(args.inp))
        out = {"effective_evidence_level": int(lvl), "label": lvl.label, "reasons": why}
    elif args.cmd == "scan":
        contras = ContradictionScanner().scan(_pattern(args.inp), _contract(args.contract))
        out = {"contradictions": [c.__dict__ for c in contras], "count": len(contras)}
    elif args.cmd == "gate":
        store = ProvenanceStore(args.db) if args.db else None
        dec = PromotionGate(store).evaluate(
            _pattern(args.inp), _contract(args.contract), vi_approval=args.vi_approval
        )
        out = dec.to_dict()
    elif args.cmd == "ingest":
        store = ProvenanceStore(args.db)
        ver = store.add_pattern(_pattern(args.inp))
        out = {"ingested": args.inp, "version": ver, "db": args.db}
    else:  # pragma: no cover
        p.error("unknown command")
        return 2

    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only ledger integrity checker (Trinity Auditor tool).

Verifies the tamper-evidence properties of an MΣBUS JSONL ledger stream without
writing anything:

  1. canonical JSON, one record per line;
  2. every record carries a `fingerprint` that recomputes from its content
     (detects in-place content tampering of a record);
  3. the `prev_fingerprint` hash chain is unbroken (detects deletion, reordering,
     or truncation of records — the attacks per-record fingerprints alone miss);
  4. only the FINAL line may be a partial/truncated write (the append-only
     invariant); that case is reported, not treated as corruption.

This is an out-of-loop verifier: it reuses `record_fingerprint` from the live
transport so it stays in lockstep with how records are actually stamped. It never
appends, never mutates, never starts a network. Exit code 0 = pass, 1 = integrity
violation, 2 = usage/IO error.

Usage:
    python scripts/check_ledger_integrity.py <stream.jsonl> [<stream2.jsonl> ...]
    python scripts/check_ledger_integrity.py --json data/ledger/predictions.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Reuse the live stamping logic so the checker can never drift from production.
try:
    from ai_chi.bus.transports.file_transport import record_fingerprint
except Exception:  # pragma: no cover - fallback keeps the checker self-contained
    import hashlib

    def record_fingerprint(record: dict[str, Any]) -> str:
        body = {k: v for k, v in record.items() if k != "fingerprint"}
        encoded = json.dumps(body, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def check_stream(path: Path) -> list[str]:
    """Return a list of integrity problems for one stream (empty = clean)."""
    problems: list[str] = []
    if not path.exists():
        return [f"{path.name}: file not found"]

    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines(keepends=True)
    prev_fp = ""
    for n, line in enumerate(lines, start=1):
        is_final_partial = n == len(lines) and not line.endswith("\n")
        text = line.strip()
        if not text:
            continue
        try:
            rec = json.loads(text)
        except json.JSONDecodeError as exc:
            if is_final_partial:
                problems.append(f"{path.name}: line {n} is a partial trailing "
                                f"write (append-only tail; tolerated, not fatal): {exc}")
                continue
            problems.append(f"{path.name}: line {n} invalid JSON: {exc}")
            continue

        if "fingerprint" not in rec:
            problems.append(f"{path.name}: line {n} missing fingerprint (unstamped record)")
            continue
        recomputed = record_fingerprint(rec)
        if recomputed != rec["fingerprint"]:
            problems.append(f"{path.name}: line {n} fingerprint mismatch "
                            f"(content tampered)")
        if rec.get("prev_fingerprint", "") != prev_fp:
            problems.append(f"{path.name}: line {n} chain break "
                            f"(deletion/reorder/truncation upstream)")
        prev_fp = rec["fingerprint"]

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only MΣBUS ledger integrity checker.")
    parser.add_argument("streams", nargs="+", help="JSONL ledger stream file(s) to verify")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args(argv)

    all_problems: dict[str, list[str]] = {}
    for s in args.streams:
        p = Path(s)
        probs = check_stream(p)
        # A lone tolerated partial-tail note is not an integrity failure.
        fatal = [x for x in probs if "tolerated, not fatal" not in x]
        all_problems[str(p)] = probs
        if not args.json:
            status = "PASS" if not fatal else "FAIL"
            print(f"[{status}] {p}")
            for x in probs:
                print(f"    - {x}")

    fatal_any = any(
        any("tolerated, not fatal" not in x for x in probs)
        for probs in all_problems.values()
    )
    if args.json:
        print(json.dumps({
            "schema": "digivichi.trinity.ledger-integrity-check.v0",
            "results": all_problems,
            "integrity": "fail" if fatal_any else "pass",
        }, ensure_ascii=False, indent=2))
    return 1 if fatal_any else 0


if __name__ == "__main__":
    sys.exit(main())

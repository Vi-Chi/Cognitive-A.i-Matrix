#!/usr/bin/env python3
"""DreamLens Evaluation Harness

This script loads deterministic test fixtures, feeds them to the OllamaDreamLens,
and writes the proposed Contradictions to an evidence log in JSONL format.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai_chi.bus import PredictionRecord
from ai_chi.urbi.dream.lens import OllamaDreamLens

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
_LOG = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

FIXTURES_PATH = ROOT_DIR / "ai_chi" / "tests" / "fixtures" / "dream_lens_eval_records.json"
REPORTS_DIR = ROOT_DIR / "_PROJECT_KNOWLEDGE_BASE" / "reports"


def load_fixtures(path: Path) -> list[PredictionRecord]:
    if not path.exists():
        _LOG.error(f"Fixtures not found at {path}")
        sys.exit(1)
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    records = []
    for row in data:
        records.append(PredictionRecord(**row))
    return records


def main():
    parser = argparse.ArgumentParser(description="Evaluate DreamLens Proposer")
    parser.add_argument("--dry-run", action="store_true", help="Parse fixtures but do not call the model.")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"DREAM_LENS_EVALUATION_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.jsonl"

    _LOG.info(f"Loading fixtures from {FIXTURES_PATH.relative_to(ROOT_DIR)}")
    records = load_fixtures(FIXTURES_PATH)
    _LOG.info(f"Loaded {len(records)} PredictionRecords.")

    if args.dry_run:
        _LOG.info("Dry run complete. Exiting.")
        sys.exit(0)

    lens = OllamaDreamLens()
    
    if not lens.available():
        _LOG.error(f"Ollama does not appear to be running or the model '{lens.model}' is unavailable at {lens.base_url}")
        sys.exit(1)

    _LOG.info(f"Sending records to OllamaDreamLens (model: {lens.model})...")
    contradictions = lens.propose(records)
    
    _LOG.info(f"Received {len(contradictions)} contradiction hints.")
    
    with open(report_path, "w", encoding="utf-8") as f:
        # Write input batch context
        f.write(json.dumps({
            "type": "evaluation_run",
            "timestamp": datetime.now().isoformat(),
            "model": lens.model,
            "input_records_count": len(records)
        }) + "\n")
        
        # Write output contradictions
        for c in contradictions:
            f.write(json.dumps({
                "type": "contradiction_hint",
                "claim_id": c.claim_id,
                "kind": c.kind.value,
                "severity": c.severity,
                "detail": c.detail
            }) + "\n")

    _LOG.info(f"Evidence log written to: {report_path.relative_to(ROOT_DIR)}")

if __name__ == "__main__":
    main()

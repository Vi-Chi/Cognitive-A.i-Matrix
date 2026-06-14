"""Command-line friendly offline runner for DreamLens evaluation fixtures."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_chi.urbi.dream.evaluation import (
    DEFAULT_FIXTURE_DIR,
    evaluate_fixtures,
    load_fixtures,
    summarize_results,
)


def run_fixture_harness(fixture_dir: str | Path = DEFAULT_FIXTURE_DIR) -> dict[str, Any]:
    fixtures = load_fixtures(fixture_dir)
    results = evaluate_fixtures(fixtures)
    return {
        "fixture_dir": str(Path(fixture_dir)),
        "results": [result.to_dict() for result in results],
        "summary": summarize_results(results),
        "action_allowed": False,
    }


def main() -> int:
    payload = run_fixture_harness()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

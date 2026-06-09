#!/usr/bin/env python3
"""Validate the Phase 0 Project Autopoiesis repository."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "README.md",
    "LICENSE",
    "MASTER_CONTEXT.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    ".gitattributes",
    ".gitignore",
    ".github/workflows/validate.yml",
    "docs/00-thesis/00-autopoiesis-thesis.md",
    "docs/00-thesis/01-integrity-vs-economic-pressure.md",
    "docs/00-thesis/02-compute-metabolism-model.md",
    "docs/10-network-map/10-network-role-map.md",
    "docs/10-network-map/11-icp-role-in-autopoiesis.md",
    "docs/10-network-map/12-akash-compute-procurement.md",
    "docs/10-network-map/13-golem-task-execution.md",
    "docs/10-network-map/14-bittensor-usefulness-markets.md",
    "docs/10-network-map/15-storage-and-public-memory-options.md",
    "docs/20-economic-loop/20-economic-loop.md",
    "docs/20-economic-loop/21-compute-cost-estimator.md",
    "docs/20-economic-loop/22-task-value-estimator.md",
    "docs/20-economic-loop/23-budget-and-treasury-policy.md",
    "docs/30-v0-prototype/30-autopoiesis-v0-scope.md",
    "docs/30-v0-prototype/31-icp-compute-registry-spec.md",
    "docs/40-procurement/40-procurement-experiment-plan.md",
    "docs/50-cognitive-matrix-integration/50-cognitive-matrix-integration.md",
    "docs/50-cognitive-matrix-integration/51-integrity-gate-for-economic-actions.md",
    "docs/50-cognitive-matrix-integration/52-out-of-loop-audit-of-autopoietic-decisions.md",
    "docs/60-services-and-revenue/60-safe-service-candidate-filter.md",
    "docs/70-sovereignty-and-safety/70-local-sovereignty-and-privacy.md",
    "specs/provider-capability.schema.json",
    "specs/job-lifecycle.schema.json",
    "specs/treasury-policy.schema.json",
    "specs/compute-decision.schema.json",
    "prototypes/icp-compute-registry/README.md",
    "prototypes/treasury-simulator/README.md",
    "prototypes/local-vs-remote-router/README.md",
    "research/icp/README.md",
    "research/akash/README.md",
    "research/golem/README.md",
    "research/bittensor/README.md",
    "research/ethereum/README.md",
    "research/storage/README.md",
    "reports/autopoiesis-discovery-phase0.md",
]

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|password|secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
]

TEXT_SUFFIXES = {".md", ".json", ".py", ".yml", ".yaml", ".txt", ".gitignore", ".gitattributes"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_required_paths() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("missing required paths:\n" + "\n".join(f"  - {path}" for path in missing))


def check_json_schemas() -> None:
    for path in sorted((ROOT / "specs").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")
        if data.get("$schema") is None:
            fail(f"{path.relative_to(ROOT)} lacks $schema")
        if data.get("type") != "object":
            fail(f"{path.relative_to(ROOT)} must describe an object schema")


def check_secret_patterns() -> None:
    findings: list[str] = []
    ignored_parts = {".git"}
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ignored_parts.intersection(path.parts):
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    if findings:
        fail("possible committed secret pattern:\n" + "\n".join(f"  - {item}" for item in findings))


def check_readme_links() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for phrase in ["MASTER_CONTEXT.md", "AUTOPOIESIS_REAL_SPENDING=false", "Vi-Chi/project-autopoiesis"]:
        if phrase not in readme:
            fail(f"README.md missing expected phrase: {phrase}")


def main() -> int:
    check_required_paths()
    check_json_schemas()
    check_secret_patterns()
    check_readme_links()
    print("Project Autopoiesis validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

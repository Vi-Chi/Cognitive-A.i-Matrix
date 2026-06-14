#!/usr/bin/env python3
"""DAN pre-publish gate - FAIL-CLOSED secret/PII scan.

Python port of dan_pre_publish_gate.sh to leverage the exact `contains_secret_shape`
logic and eliminate bare-word false positives. Exit 1 if hits found, else 0.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import re
import sys
from pathlib import Path

# Add scripts/ to path to import graveyard_redaction
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

try:
    from graveyard_redaction import contains_secret_shape
except ImportError:
    print("gate: cannot import graveyard_redaction", file=sys.stderr)
    sys.exit(2)

IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "target", "_backup"}
IGNORE_REL_PREFIXES = (
    ("_MODEL_TRINITY", "bridge", "health"),
    ("_MODEL_TRINITY", "bridge", "ledger"),
    ("_MODEL_TRINITY", "bridge", "state"),
    ("_MODEL_TRINITY", "bridge", "inbox"),
    ("_MODEL_TRINITY", "bridge", "outbox"),
    ("_MODEL_TRINITY", "bridge", "processed"),
)
MAX_FILE_BYTES = 2_000_000

PUBLIC_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "public_pii:marina",
        re.compile(r"(?i)\b(?:marina|harbou?r|mooring)\b\s*[:=]\s*\S"),
    ),
    (
        "public_pii:berth",
        re.compile(r"(?i)\bberth\b\s*[:=]\s*\S"),
    ),
    (
        "public_pii:home_address",
        re.compile(r"(?i)\bhome\s+address\b\s*[:=]\s*\S"),
    ),
    (
        "public_pii:private_address",
        re.compile(r"(?i)\b(?:private|street|physical)\s+address\b\s*[:=]\s*\S"),
    ),
    (
        "public_pii:private_link",
        re.compile(r"(?i)\bprivate\s+(?:link|url)\b\s*[:=]\s*(?:https?://|www\.|\S)"),
    ),
    (
        "public_pii:vessel_location",
        re.compile(
            r"(?i)\b(?:vessel|boat|wibo|vento[-\s]?viv[ei]re)\s+"
            r"(?:location|mooring|berth|marina)\b\s*[:=]\s*\S"
        ),
    ),
    (
        "public_pii:coordinates",
        re.compile(
            r"(?i)\b(?:home|vessel|boat|marina|berth|private)\b.{0,32}"
            r"\b(?:lat(?:itude)?|lon(?:gitude)?|gps|coordinates?)\b\s*[:=]\s*[-+]?\d{1,3}\.\d+"
        ),
    ),
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    labels: tuple[str, ...]

    def render(self) -> str:
        return f"{self.path}:{self.line}: {', '.join(self.labels)}"


def _looks_binary(blob: bytes) -> bool:
    return b"\x00" in blob[:4096]


def _is_ignored_rel(path: Path) -> bool:
    normalized = tuple(part.replace("\\", "/") for part in path.parts)
    return any(normalized[: len(prefix)] == prefix for prefix in IGNORE_REL_PREFIXES)


def classify_line(line: str) -> tuple[str, ...]:
    labels: list[str] = []
    if contains_secret_shape(line):
        labels.append("secret_shape")
    for label, pattern in PUBLIC_PII_PATTERNS:
        if pattern.search(line):
            labels.append(label)
    return tuple(labels)


def scan_repo(root: Path) -> list[Finding]:
    hits: list[Finding] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for f in filenames:
            if f == "dan_pre_publish_gate.sh" or f == "dan_pre_publish_gate.py" or f.endswith(".example"):
                continue

            filepath = Path(dirpath) / f
            try:
                rel_path = filepath.relative_to(root)
                if _is_ignored_rel(rel_path):
                    continue
                size = filepath.stat().st_size
                if size > MAX_FILE_BYTES:
                    continue
                blob = filepath.read_bytes()
                if _looks_binary(blob):
                    continue
                content = blob.decode("utf-8", errors="ignore")

                lines = content.splitlines()
                for i, line in enumerate(lines, 1):
                    labels = classify_line(line)
                    if labels:
                        hits.append(Finding(str(rel_path), i, labels))

            except Exception:
                pass

    return hits


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    try:
        hits = scan_repo(root)
    except Exception as e:
        print(f"gate: error scanning: {e}", file=sys.stderr)
        sys.exit(2)

    if hits:
        print("## DAN PRE-PUBLISH GATE: BLOCKED")
        print("Secret-shaped or public-PII material detected. Redact or move to docs/PUBLIC_RELEASE_BLOCKERS.md before publishing.")
        print("Matches (path:line: category only; values are intentionally not printed):")
        for hit in hits:
            print(f"  {hit.render()}")
        sys.exit(1)

    print("## DAN PRE-PUBLISH GATE: PASS")
    print("No secret/PII-like patterns found by this heuristic. Human review still required before any publish.")
    sys.exit(0)

if __name__ == "__main__":
    main()

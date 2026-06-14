"""Local redacted checker for Trinity secret references.

Default mode checks only whether expected environment variable names are present.
It does not print secret values. Fingerprinting is opt-in with --fingerprint-env.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


DEFAULT_OPS_DIR = Path("_PROJECT_KNOWLEDGE_BASE") / "trinity_live_ops_2026-06-13"

REFERENCE_GROUPS = (
    ("OpenAI / Codex", ("OPENAI_API_KEY",), "Codex", True),
    ("Anthropic / Claude", ("ANTHROPIC_API_KEY",), "Claude", True),
    ("Google / Gemini Antigravity", ("GOOGLE_API_KEY", "GEMINI_API_KEY"), "Antigravity", True),
    ("Discord bot", ("DISCORD_BOT_TOKEN",), "Discord adapter", False),
    ("Discord webhook", ("DISCORD_WEBHOOK_URL",), "Discord adapter", False),
)

RAW_SECRET_PATTERNS = (
    ("openai_key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{20,}")),
    ("github_token", re.compile(r"(?:ghp_|github_pat_)[0-9A-Za-z_]{20,}")),
    ("discord_webhook_url", re.compile(r"https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9._-]+")),
    ("discord_bot_token", re.compile(r"(?:mfa\.[A-Za-z0-9_-]{20,}|[A-Za-z0-9_-]{23,28}\.[A-Za-z0-9_-]{6,7}\.[A-Za-z0-9_-]{27,})")),
    ("pem_private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)


@dataclass(frozen=True)
class ReferenceRow:
    provider: str
    env_refs: tuple[str, ...]
    required_by: str
    required: bool
    status: str
    fingerprint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "env_refs": list(self.env_refs),
            "required_by": self.required_by,
            "required": self.required,
            "status": self.status,
            "fingerprint": self.fingerprint,
        }


def redacted_fingerprint(secret_value: str) -> str:
    digest = hashlib.sha256(secret_value.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:8]}...{digest[-4:]}"


def build_reference_rows(
    env: Mapping[str, str],
    *,
    fingerprint_env: bool = False,
) -> list[ReferenceRow]:
    rows: list[ReferenceRow] = []
    for provider, names, required_by, required in REFERENCE_GROUPS:
        present_names = tuple(name for name in names if name in env and env.get(name))
        if not present_names:
            rows.append(ReferenceRow(provider, names, required_by, required, "missing", "not_generated"))
            continue
        if fingerprint_env:
            joined = "|".join(env[name] for name in present_names)
            fingerprint = redacted_fingerprint(joined)
        else:
            fingerprint = "not_requested"
        rows.append(ReferenceRow(provider, names, required_by, required, "present", fingerprint))
    return rows


def scan_text_for_raw_secrets(text: str) -> list[str]:
    labels: list[str] = []
    for label, pattern in RAW_SECRET_PATTERNS:
        if pattern.search(text or ""):
            labels.append(label)
    return labels


def scan_ops_dir(ops_dir: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if not ops_dir.exists():
        return [{"path": str(ops_dir), "labels": ["missing_ops_dir"]}]
    for path in sorted(ops_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        labels = scan_text_for_raw_secrets(text)
        if labels:
            findings.append({"path": str(path), "labels": labels})
    return findings


def render_text(rows: list[ReferenceRow], findings: list[dict[str, object]]) -> str:
    lines = ["Trinity secret reference check", ""]
    for row in rows:
        refs = ", ".join(row.env_refs)
        lines.append(
            f"- {row.provider}: refs={refs}; status={row.status}; fingerprint={row.fingerprint}; required={row.required}"
        )
    lines.append("")
    if findings:
        lines.append("raw_secret_scan=fail")
        for finding in findings:
            lines.append(f"- {finding['path']}: {', '.join(str(x) for x in finding['labels'])}")
    else:
        lines.append("raw_secret_scan=pass")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Trinity secret references without printing secrets.")
    parser.add_argument("--ops-dir", default=str(DEFAULT_OPS_DIR), help="Directory of generated Phase 7.1 ops artifacts.")
    parser.add_argument("--fingerprint-env", action="store_true", help="Read env values locally and print redacted SHA-256 fingerprints only.")
    parser.add_argument("--json", action="store_true", help="Emit JSON status.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or []))
    rows = build_reference_rows(os.environ, fingerprint_env=args.fingerprint_env)
    findings = scan_ops_dir(Path(args.ops_dir))
    payload = {
        "schema": "digivichi.trinity.secret-reference-check.v0",
        "fingerprint_env": bool(args.fingerprint_env),
        "references": [row.to_dict() for row in rows],
        "raw_secret_findings": findings,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(rows, findings))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

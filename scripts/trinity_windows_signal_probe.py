"""Scoped Windows signal probe for Trinity DAN handoff hints.

This probe is read-only. It checks:

- Trinity bridge queue counts;
- scoped Claude log keyword counts;
- Windows push-notification event metadata counts.

It does not read raw notification database contents, credential files, provider
tokens, or app config bodies.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_SCRIPT = REPO_ROOT / "scripts" / "trinity_bridge.py"
CLAUDE_LOG = Path(os.environ.get("APPDATA", "")) / "Claude" / "logs" / "main.log"
PUSH_LOG = "Microsoft-Windows-PushNotification-Platform/Operational"
CLAUDE_PATTERNS = {
    "session_limit": re.compile(r"\b(session limit|limit reached|baseline quota|quota|rate limit)\b", re.I),
    "sleep_state": re.compile(r"\b(sleeping|sleep|idle|session .* idle)\b", re.I),
    "dan_handoff": re.compile(r"\b(DAN|handoff|Trinity|bridge packet|outbox|inbox)\b", re.I),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_json(command: list[str], *, timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc)}
    if proc.returncode != 0:
        return {
            "ok": False,
            "exit_code": proc.returncode,
            "stderr_tail": proc.stderr[-1000:],
            "stdout_tail": proc.stdout[-1000:],
        }
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid_json", "stdout_tail": proc.stdout[-1000:]}
    parsed["ok"] = True
    return parsed


def bridge_status() -> dict[str, Any]:
    return run_json([sys.executable, str(BRIDGE_SCRIPT), "--status"])


def tail_lines(path: Path, *, max_lines: int) -> list[tuple[int, str]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = max(0, len(lines) - max_lines)
    return [(start + index + 1, line) for index, line in enumerate(lines[start:])]


def claude_log_signals(max_lines: int) -> dict[str, Any]:
    counts = Counter()
    line_numbers: dict[str, list[int]] = {name: [] for name in CLAUDE_PATTERNS}
    for line_number, line in tail_lines(CLAUDE_LOG, max_lines=max_lines):
        for name, pattern in CLAUDE_PATTERNS.items():
            if pattern.search(line):
                counts[name] += 1
                line_numbers[name].append(line_number)
    return {
        "path": str(CLAUDE_LOG),
        "exists": CLAUDE_LOG.exists(),
        "lines_scanned": max_lines if CLAUDE_LOG.exists() else 0,
        "counts": dict(counts),
        "line_numbers": {key: value[-5:] for key, value in line_numbers.items() if value},
    }


def push_notification_event_metadata(since_minutes: int) -> dict[str, Any]:
    ps = (
        "$start=(Get-Date).AddMinutes(-{minutes}); "
        "Get-WinEvent -FilterHashtable @{{LogName='{log}'; StartTime=$start}} "
        "-ErrorAction SilentlyContinue | "
        "Select-Object TimeCreated,Id,ProviderName,LevelDisplayName | "
        "ConvertTo-Json -Compress"
    ).format(minutes=int(since_minutes), log=PUSH_LOG)
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-Command", ps],
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        return {"ok": False, "log": PUSH_LOG, "error": type(exc).__name__, "detail": str(exc)}
    if proc.returncode != 0:
        return {"ok": False, "log": PUSH_LOG, "exit_code": proc.returncode, "stderr_tail": proc.stderr[-1000:]}
    raw = proc.stdout.strip()
    if not raw:
        events: list[dict[str, Any]] = []
    else:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"ok": False, "log": PUSH_LOG, "error": "invalid_json", "stdout_tail": raw[-1000:]}
        events = parsed if isinstance(parsed, list) else [parsed]
    by_id = Counter(str(event.get("Id", "unknown")) for event in events if isinstance(event, dict))
    latest = events[0].get("TimeCreated") if events and isinstance(events[0], dict) else None
    return {
        "ok": True,
        "log": PUSH_LOG,
        "since_minutes": since_minutes,
        "events": len(events),
        "by_id": dict(by_id),
        "latest_time": latest,
        "message_text_read": False,
    }


def classify(status: dict[str, Any], log_signals: dict[str, Any]) -> list[str]:
    signals: list[str] = []
    outbox = status.get("outbox") if isinstance(status.get("outbox"), dict) else {}
    if any(int(value or 0) > 0 for value in outbox.values()):
        signals.append("bridge_outbox_pending")
    counts = log_signals.get("counts", {})
    if counts.get("session_limit", 0):
        signals.append("claude_session_limit_hint")
    if counts.get("dan_handoff", 0):
        signals.append("dan_handoff_hint")
    return signals


def main() -> int:
    parser = argparse.ArgumentParser(description="Scoped Windows signal probe for Trinity DAN handoff hints.")
    parser.add_argument("--since-minutes", type=int, default=30)
    parser.add_argument("--claude-log-lines", type=int, default=500)
    args = parser.parse_args()

    status = bridge_status()
    log_signals = claude_log_signals(args.claude_log_lines)
    events = push_notification_event_metadata(args.since_minutes)
    payload = {
        "schema": "digivichi.trinity.windows-signal-probe.v0",
        "created_at": utc_now(),
        "repo_root": str(REPO_ROOT),
        "bridge": status,
        "claude_log": log_signals,
        "windows_push_notifications": events,
        "signals": classify(status, log_signals),
        "privacy": {
            "raw_notification_text_read": False,
            "credential_files_read": False,
            "app_config_mutated": False,
            "service_started": False,
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

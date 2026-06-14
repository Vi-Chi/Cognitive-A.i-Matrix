#!/usr/bin/env python3
"""Trinity Signal Intake (Bounded Single Pass)

Wires up structured external signals (Windows probes, JSON inputs) and routes
them to the Trinity bridge quota events ledger.

Adheres strictly to the Trinity Signal State Machine:
- No `while True:` background polling.
- Bounded single-pass execution.
- Reads only structured metadata JSON, never raw notification bodies.
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_chi.utils.filelock import InterprocessLock

_LOG = logging.getLogger("signal_intake")
BRIDGE_ROOT = ROOT / "_MODEL_TRINITY" / "bridge"

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def run_windows_probe(since_minutes: int, log_lines: int) -> dict[str, Any] | None:
    probe_script = ROOT / "scripts" / "trinity_windows_signal_probe.py"
    cmd = [
        sys.executable,
        str(probe_script),
        "--since-minutes", str(since_minutes),
        "--claude-log-lines", str(log_lines),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(proc.stdout)
    except subprocess.CalledProcessError as e:
        _LOG.error("Windows signal probe failed (exit %d): %s", e.returncode, e.stderr)
        return None
    except json.JSONDecodeError as e:
        _LOG.error("Failed to parse Windows signal probe JSON: %s", e)
        return None

def append_quota_event(payload: dict[str, Any]) -> None:
    event_path = BRIDGE_ROOT / "quota" / "events" / "windows_signals.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    with InterprocessLock(event_path):
        with event_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
            handle.flush()

def process_structured_payload(payload: dict[str, Any]) -> None:
    # Safely strip any raw bodies if they snuck in
    safe_payload = {k: v for k, v in payload.items() if k not in ("message", "body", "text", "raw_sensor", "notification_text")}
    
    signals = safe_payload.get("signals", [])
    if not signals and "status" not in safe_payload:
        _LOG.info("No actionable signals found in payload.")
        return

    agent = "claude"
    if isinstance(signals, list) and any("codex" in str(s).lower() for s in signals):
        agent = "codex"
    elif "agent" in safe_payload:
        agent = str(safe_payload["agent"]).lower()

    reason = ",".join(str(s) for s in signals) if signals else str(safe_payload.get("status", "unknown_signal"))

    event = {
        "schema_version": "digivichi.trinity.quota.event.v0",
        "id": f"evt_probe_{uuid.uuid4().hex[:8]}",
        "created_at": safe_payload.get("created_at", utc_now()),
        "agent": agent,
        "record_source": safe_payload.get("record_source", "structured_signal_intake"),
        "reason": reason,
        "privacy": {
            "raw_notification_text_read": False,
            "credential_files_read": False,
        },
    }
    append_quota_event(event)
    _LOG.info("Successfully ingested structured quota event for agent '%s' with reason: %s", agent, reason)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trinity Signal Intake Daemon (Single Pass)")
    parser.add_argument("--run-windows-probe", action="store_true", help="Run the Windows signal probe directly and consume its output")
    parser.add_argument("--since-minutes", type=int, default=30, help="For --run-windows-probe: look back window")
    parser.add_argument("--claude-log-lines", type=int, default=500, help="For --run-windows-probe: lines to check")
    parser.add_argument("--stdin", action="store_true", help="Read structured JSON payloads from stdin")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    if not args.run_windows_probe and not args.stdin:
        _LOG.info("No action requested. Use --run-windows-probe or --stdin.")
        parser.print_help()
        return 0

    if args.run_windows_probe:
        _LOG.info("Running Windows signal probe...")
        payload = run_windows_probe(args.since_minutes, args.claude_log_lines)
        if payload:
            process_structured_payload(payload)

    if args.stdin:
        _LOG.info("Reading structured JSON from stdin...")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                process_structured_payload(payload)
            except json.JSONDecodeError:
                _LOG.warning("Invalid JSON received on stdin, skipping line.")
            except Exception as exc:
                _LOG.exception("Error processing ingest line: %s", exc)

    return 0

if __name__ == "__main__":
    sys.exit(main())

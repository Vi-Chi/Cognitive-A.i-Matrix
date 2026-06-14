"""Arbitration layer for the local Trinity bridge.

The arbitrator scans pending outbox packets before routing. It validates packet
shape, applies capability manifests, creates claim locks, writes compact state
deltas, and quarantines packets that are stale, superseded, invalid, blocked, or
approval-gated. It does not execute packet contents, call models, install tools,
or mutate app-level configuration.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import trinity_bridge
    import trinity_executor
except ImportError:  # pragma: no cover - defensive when imported from tests
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import trinity_bridge  # type: ignore
    import trinity_executor  # type: ignore


SCHEMA = "digivichi.trinity.arbitration.v0"
CAPABILITIES_SCHEMA = "digivichi.trinity.capabilities.v0"
DEFAULT_ARBITRATION_LEDGER = Path("ledger") / "arbitration-ledger.jsonl"
DEFAULT_LATEST_STATE = Path("state") / "latest-arbitration.json"
DEFAULT_CLAIMS_DIR = Path("claims")
DEFAULT_COMPACT_DIR = Path("state") / "compact-handoffs"
DEFAULT_CAPABILITIES = Path("agent-capabilities.json")
ARBITRATOR_ID = "trinity_arbitrator"

SAFE = "safe"
NEEDS_HUMAN = "needs-human"
BLOCKED = "blocked"
STALE = "stale"
SUPERSEDED = "superseded"
INVALID = "invalid"
QUARANTINE_BUCKETS = {
    NEEDS_HUMAN: "needs_human",
    BLOCKED: "blocked",
    STALE: "stale",
    SUPERSEDED: "superseded",
    INVALID: "arbitration_rejected",
}
PASSIVE_KINDS = {
    "handoff",
    "review",
    "audit",
    "patch_plan",
    "build_report",
    "cycle_summary",
    "arbitration_summary",
    "execution_result",
}


class ArbitrationError(Exception):
    """Raised when the arbitration runtime cannot safely proceed."""


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def arbitrator_config(config: dict[str, Any]) -> dict[str, Any]:
    raw = config.get("arbitrator")
    return raw if isinstance(raw, dict) else {}


def arbitration_enabled(config: dict[str, Any]) -> bool:
    return bool(arbitrator_config(config).get("enabled", True))


def arbitration_ledger_path(root: Path, config: dict[str, Any]) -> Path:
    configured = arbitrator_config(config).get("ledger_path", str(DEFAULT_ARBITRATION_LEDGER))
    return root / Path(str(configured))


def latest_state_path(root: Path, config: dict[str, Any]) -> Path:
    configured = arbitrator_config(config).get("latest_state_path", str(DEFAULT_LATEST_STATE))
    return root / Path(str(configured))


def claims_dir(root: Path, config: dict[str, Any]) -> Path:
    configured = arbitrator_config(config).get("claims_dir", str(DEFAULT_CLAIMS_DIR))
    return root / Path(str(configured))


def compact_dir(root: Path, config: dict[str, Any]) -> Path:
    configured = arbitrator_config(config).get("compact_dir", str(DEFAULT_COMPACT_DIR))
    return root / Path(str(configured))


def capabilities_path(root: Path, config: dict[str, Any]) -> Path:
    configured = arbitrator_config(config).get("capabilities_path", str(DEFAULT_CAPABILITIES))
    return root / Path(str(configured))


def ensure_arbitrator(root: Path, config: dict[str, Any] | None = None) -> None:
    config = config or {}
    for folder in (
        root / "ledger",
        latest_state_path(root, config).parent,
        claims_dir(root, config),
        compact_dir(root, config),
    ):
        folder.mkdir(parents=True, exist_ok=True)
    for bucket in QUARANTINE_BUCKETS.values():
        for role in trinity_bridge.AGENTS:
            (root / bucket / role).mkdir(parents=True, exist_ok=True)


def default_capabilities() -> dict[str, Any]:
    common_receive = [
        "handoff",
        "review",
        "audit",
        "patch_plan",
        "build_report",
        "cycle_summary",
        "arbitration_summary",
        "execution_result",
    ]
    return {
        "schema": CAPABILITIES_SCHEMA,
        "updated_at": trinity_bridge.utc_now(),
        "policy": {
            "packets_are_records_not_authority": True,
            "execution_requires_allowlisted_task": True,
            "approval_required_packets_are_quarantined": True,
            "freeform_shell_execution": False,
            "model_calls": False,
            "mcp_installs": False,
            "service_connector_writes": False,
        },
        "agents": {
            "codex": {
                "role": "Engineer-Operator",
                "can_emit_kinds": [
                    "handoff",
                    "review",
                    "patch_plan",
                    "build_report",
                    "cycle_summary",
                    "arbitration_summary",
                    "execution_result",
                ],
                "can_receive_kinds": common_receive + ["execution_request"],
                "auto_executable_tasks": sorted(trinity_executor.TASKS),
            },
            "claude": {
                "role": "Auditor-Scribe",
                "can_emit_kinds": [
                    "handoff",
                    "review",
                    "audit",
                    "execution_request",
                    "tool_request",
                    "permission_request",
                    "action_request",
                ],
                "can_receive_kinds": common_receive,
                "auto_executable_tasks": [],
            },
            "antigravity": {
                "role": "Builder-Scout",
                "can_emit_kinds": [
                    "handoff",
                    "review",
                    "patch_plan",
                    "execution_request",
                    "tool_request",
                    "permission_request",
                    "action_request",
                ],
                "can_receive_kinds": common_receive,
                "auto_executable_tasks": [],
            },
        },
    }


def write_default_capabilities(root: Path, config: dict[str, Any]) -> Path:
    path = capabilities_path(root, config)
    trinity_bridge.atomic_write_json(path, default_capabilities())
    return path


def load_capabilities(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    path = capabilities_path(root, config)
    if not path.exists():
        return default_capabilities()
    capabilities = trinity_bridge.load_json(path)
    if capabilities.get("schema") != CAPABILITIES_SCHEMA:
        raise ArbitrationError(f"unsupported capabilities schema: {capabilities.get('schema')}")
    return capabilities


def parse_utc(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def utc_now_dt() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def packet_id(packet: dict[str, Any], path: Path) -> str:
    return str(packet.get("handoff_id") or path.stem)


def sanitize_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)[:160]


def compact_text(value: Any, limit: int) -> str:
    text = trinity_executor.redact_sensitive(str(value or "").strip())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}\n...[truncated {len(text) - limit} chars]"


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def target_list(packet: dict[str, Any], source: str) -> list[str]:
    return trinity_bridge.normalize_targets(packet.get("to"), source)


def pending_packets(root: Path) -> list[tuple[str, Path]]:
    return list(trinity_bridge.iter_outbox_packets(root))


def superseded_ids(root: Path) -> dict[str, str]:
    superseded: dict[str, str] = {}
    for _source, path in pending_packets(root):
        try:
            packet = trinity_bridge.load_json(path)
        except trinity_bridge.BridgeError:
            continue
        newer_id = packet_id(packet, path)
        for old_id in normalize_list(packet.get("supersedes")):
            old_id = old_id.strip()
            if old_id and old_id != newer_id:
                superseded[old_id] = newer_id
    return superseded


def capability_issue(packet: dict[str, Any], capabilities: dict[str, Any]) -> str | None:
    source = str(packet.get("from") or "").lower()
    kind = str(packet.get("kind") or "handoff").lower()
    agents = capabilities.get("agents")
    if not isinstance(agents, dict):
        return "capabilities manifest lacks agents object"
    source_caps = agents.get(source)
    if not isinstance(source_caps, dict):
        return f"source {source or '<missing>'} has no capability manifest"
    emit_kinds = set(normalize_list(source_caps.get("can_emit_kinds")))
    if kind not in emit_kinds:
        return f"source {source} cannot emit kind {kind}"
    try:
        targets = target_list(packet, source)
    except trinity_bridge.BridgeError as exc:
        return str(exc)
    for target in targets:
        target_caps = agents.get(target)
        if not isinstance(target_caps, dict):
            return f"target {target} has no capability manifest"
        receive_kinds = set(normalize_list(target_caps.get("can_receive_kinds")))
        if kind not in receive_kinds:
            return f"target {target} cannot receive kind {kind}"
    return None


def validate_budget(packet: dict[str, Any]) -> str | None:
    if "budget" not in packet:
        return None
    budget = packet.get("budget")
    if not isinstance(budget, dict):
        return "budget must be an object"
    for key in ("max_tokens", "max_runtime_seconds", "max_iterations"):
        if key in budget:
            try:
                value = int(budget[key])
            except (TypeError, ValueError):
                return f"budget.{key} must be an integer"
            if value < 0:
                return f"budget.{key} must be non-negative"
    return None


def validate_execution_request(packet: dict[str, Any], capabilities: dict[str, Any]) -> str | None:
    execution = packet.get("execution")
    if not isinstance(execution, dict):
        return "execution_request requires structured execution object"
    if execution.get("schema", trinity_executor.REQUEST_SCHEMA) != trinity_executor.REQUEST_SCHEMA:
        return f"unsupported execution schema: {execution.get('schema')}"
    task_id = str(execution.get("task_id") or "").strip()
    if not task_id:
        return "execution.task_id is required"
    codex_caps = capabilities.get("agents", {}).get("codex", {})
    allowed_tasks = set(normalize_list(codex_caps.get("auto_executable_tasks")))
    if task_id not in allowed_tasks:
        return f"execution.task_id {task_id} is not allowed by capability manifest"
    try:
        trinity_executor.validate_execution(packet, execution)
    except (trinity_executor.ExecutorError, trinity_bridge.BridgeError) as exc:
        return str(exc)
    return None


def claim_path(root: Path, config: dict[str, Any], handoff_id: str) -> Path:
    return claims_dir(root, config) / f"{sanitize_id(handoff_id)}.json"


def claim_is_expired(claim: dict[str, Any], config: dict[str, Any]) -> bool:
    ttl = int(arbitrator_config(config).get("claim_ttl_seconds", 3600))
    created = parse_utc(claim.get("claimed_at"))
    if created is None:
        return True
    return (utc_now_dt() - created).total_seconds() > ttl


def claim_issue(root: Path, config: dict[str, Any], handoff_id: str) -> str | None:
    path = claim_path(root, config, handoff_id)
    if not path.exists():
        return None
    try:
        claim = trinity_bridge.load_json(path)
    except trinity_bridge.BridgeError:
        return "existing claim lock is invalid JSON"
    if claim.get("claimed_by") == ARBITRATOR_ID:
        return None
    if claim_is_expired(claim, config):
        return None
    return f"handoff is already claimed by {claim.get('claimed_by') or '<unknown>'}"


def make_claim(packet: dict[str, Any], handoff_id: str, path: Path) -> dict[str, Any]:
    return {
        "schema": "digivichi.trinity.claim-lock.v0",
        "handoff_id": handoff_id,
        "claimed_by": ARBITRATOR_ID,
        "claimed_at": trinity_bridge.utc_now(),
        "source": packet.get("from"),
        "targets": packet.get("to"),
        "kind": packet.get("kind", "handoff"),
        "source_path": str(path),
        "status": "CLAIMED_FOR_SAFE_ROUTING",
    }


def make_compact_record(record: dict[str, Any], packet: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    max_chars = int(arbitrator_config(config).get("max_compact_chars", 1200))
    return {
        "schema": "digivichi.trinity.compact-handoff.v0",
        "created_at": trinity_bridge.utc_now(),
        "handoff_id": record["handoff_id"],
        "classification": record["classification"],
        "reason": record["reason"],
        "from": packet.get("from"),
        "to": packet.get("to"),
        "kind": packet.get("kind", "handoff"),
        "priority": packet.get("priority", "MEDIUM"),
        "objective": compact_text(packet.get("objective"), 300),
        "summary": compact_text(packet.get("summary"), 500),
        "body_delta": compact_text(packet.get("body"), max_chars),
        "files_in_scope": normalize_list(packet.get("files_in_scope")),
        "requested_output": packet.get("requested_output"),
        "approval_required": bool(packet.get("approval_required") or packet.get("requires_user_approval")),
        "budget": packet.get("budget", {}),
        "expires_at": packet.get("expires_at"),
        "supersedes": normalize_list(packet.get("supersedes")),
    }


def classify_packet(
    path: Path,
    *,
    source_hint: str,
    root: Path,
    config: dict[str, Any],
    capabilities: dict[str, Any],
    superseded: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    base = {
        "schema": SCHEMA,
        "event": "arbitrated",
        "source": source_hint,
        "path": str(path),
        "created_at": trinity_bridge.utc_now(),
    }
    try:
        packet = trinity_bridge.load_json(path)
    except trinity_bridge.BridgeError as exc:
        record = {
            **base,
            "handoff_id": path.stem,
            "classification": INVALID,
            "reason": str(exc),
            "targets": [],
            "kind": "unknown",
        }
        return record, None

    handoff_id = packet_id(packet, path)
    kind = str(packet.get("kind") or "handoff").lower()
    source = str(packet.get("from") or source_hint).lower()
    targets: list[str] = []
    try:
        targets = target_list(packet, source)
    except trinity_bridge.BridgeError:
        targets = []

    record = {
        **base,
        "handoff_id": handoff_id,
        "classification": SAFE,
        "reason": "packet is safe for bridge routing",
        "targets": targets,
        "kind": kind,
    }

    if handoff_id in superseded:
        record.update(
            {
                "classification": SUPERSEDED,
                "reason": f"superseded by {superseded[handoff_id]}",
                "superseded_by": superseded[handoff_id],
            }
        )
        return record, packet

    expires_at = parse_utc(packet.get("expires_at"))
    if packet.get("expires_at") and expires_at is None:
        record.update({"classification": INVALID, "reason": "expires_at must be ISO-8601 UTC"})
        return record, packet
    if expires_at and expires_at <= utc_now_dt():
        record.update({"classification": STALE, "reason": "packet expires_at is in the past"})
        return record, packet

    budget_issue = validate_budget(packet)
    if budget_issue:
        record.update({"classification": INVALID, "reason": budget_issue})
        return record, packet

    approval_required = bool(packet.get("requires_user_approval") or packet.get("approval_required"))
    if approval_required:
        record.update({"classification": NEEDS_HUMAN, "reason": "packet requires user approval"})
        return record, packet

    if kind in trinity_bridge.ACTION_LIKE_KINDS:
        record.update({"classification": NEEDS_HUMAN, "reason": f"{kind} is action-like and needs user approval"})
        return record, packet

    try:
        normalized, warnings = trinity_bridge.validate_packet(packet, source_hint=source_hint, config=config)
    except trinity_bridge.BridgeError as exc:
        record.update({"classification": INVALID, "reason": str(exc)})
        return record, packet
    packet = normalized
    record["targets"] = normalized["to"]
    record["warnings"] = warnings

    cap_issue = capability_issue(packet, capabilities)
    if cap_issue:
        record.update({"classification": BLOCKED, "reason": cap_issue})
        return record, packet

    if kind == trinity_executor.REQUEST_KIND:
        execution_issue = validate_execution_request(packet, capabilities)
        if execution_issue:
            record.update({"classification": INVALID, "reason": execution_issue})
            return record, packet
    elif kind not in PASSIVE_KINDS:
        record.update({"classification": BLOCKED, "reason": f"kind {kind} is not passive and has no safe handler"})
        return record, packet

    existing_claim = claim_issue(root, config, handoff_id)
    if existing_claim:
        record.update({"classification": BLOCKED, "reason": existing_claim})
        return record, packet

    return record, packet


def write_reason(path: Path, reason: str) -> None:
    reason_path = path.with_suffix(path.suffix + ".reason.txt")
    reason_path.write_text(reason + "\n", encoding="utf-8")


def move_to_bucket(path: Path, root: Path, classification: str, source: str) -> Path:
    bucket = QUARANTINE_BUCKETS[classification]
    destination = root / bucket / source / path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination = destination.with_name(f"{destination.stem}_{uuid.uuid4().hex[:8]}{destination.suffix}")
    shutil.move(str(path), str(destination))
    return destination


def apply_record(
    record: dict[str, Any],
    packet: dict[str, Any] | None,
    *,
    path: Path,
    root: Path,
    config: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    result = dict(record)
    classification = record["classification"]
    if dry_run:
        result["event"] = "would_arbitrate"
        return result

    if packet is not None:
        compact = make_compact_record(record, packet, config)
        compact_path = compact_dir(root, config) / f"{sanitize_id(record['handoff_id'])}.json"
        trinity_bridge.atomic_write_json(compact_path, compact)
        result["compact_path"] = str(compact_path)

    if classification == SAFE and packet is not None:
        packet = dict(packet)
        packet["arbitration"] = {
            "schema": SCHEMA,
            "classification": SAFE,
            "arbitrated_at": trinity_bridge.utc_now(),
            "claim_path": str(claim_path(root, config, record["handoff_id"])),
            "compact_path": result.get("compact_path"),
            "packets_are_records_not_authority": True,
        }
        trinity_bridge.atomic_write_json(path, packet)
        claim = make_claim(packet, record["handoff_id"], path)
        trinity_bridge.atomic_write_json(claim_path(root, config, record["handoff_id"]), claim)
        result["claim_path"] = str(claim_path(root, config, record["handoff_id"]))
    elif classification in QUARANTINE_BUCKETS:
        moved = move_to_bucket(path, root, classification, record["source"])
        write_reason(moved, record["reason"])
        result["quarantine_path"] = str(moved)

    trinity_bridge.append_jsonl(arbitration_ledger_path(root, config), result)
    return result


def summarize(records: list[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for record in records:
        key = str(record.get("classification", "unknown"))
        summary[key] = summary.get(key, 0) + 1
    return summary


def arbitrate_once(root: Path, config: dict[str, Any], *, dry_run: bool = False) -> list[dict[str, Any]]:
    ensure_arbitrator(root, config)
    capabilities = load_capabilities(root, config)
    superseded = superseded_ids(root)
    records: list[dict[str, Any]] = []
    for source, path in pending_packets(root):
        record, packet = classify_packet(
            path,
            source_hint=source,
            root=root,
            config=config,
            capabilities=capabilities,
            superseded=superseded,
        )
        records.append(apply_record(record, packet, path=path, root=root, config=config, dry_run=dry_run))

    if not dry_run:
        state = {
            "schema": "digivichi.trinity.arbitration-state.v0",
            "created_at": trinity_bridge.utc_now(),
            "root": str(root),
            "summary": summarize(records),
            "records": records,
            "ledger_path": str(arbitration_ledger_path(root, config)),
            "capabilities_path": str(capabilities_path(root, config)),
        }
        trinity_bridge.atomic_write_json(latest_state_path(root, config), state)
    return records


def status(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    ensure_arbitrator(root, config)
    latest = latest_state_path(root, config)
    latest_state: dict[str, Any] | None = None
    if latest.exists():
        try:
            latest_state = trinity_bridge.load_json(latest)
        except trinity_bridge.BridgeError:
            latest_state = {"error": "latest arbitration state is invalid JSON"}
    return {
        "schema": "digivichi.trinity.arbitration-status.v0",
        "created_at": trinity_bridge.utc_now(),
        "enabled": arbitration_enabled(config),
        "root": str(root),
        "ledger_path": str(arbitration_ledger_path(root, config)),
        "ledger_exists": arbitration_ledger_path(root, config).exists(),
        "latest_state_path": str(latest),
        "latest_state_exists": latest.exists(),
        "claims": len(list(claims_dir(root, config).glob("*.json"))),
        "compact_handoffs": len(list(compact_dir(root, config).glob("*.json"))),
        "quarantine": {
            bucket: {
                role: len(list((root / bucket / role).glob("*.json")))
                for role in trinity_bridge.AGENTS
            }
            for bucket in QUARANTINE_BUCKETS.values()
        },
        "capabilities_path": str(capabilities_path(root, config)),
        "capabilities_exists": capabilities_path(root, config).exists(),
        "latest_state": latest_state,
    }


def load_environment(args: argparse.Namespace) -> tuple[Path, Path, dict[str, Any]]:
    root = trinity_bridge.resolve_root(args.root)
    config_path = Path(args.config).resolve() if args.config else root / "trinity-bridge.config.json"
    config = trinity_bridge.load_config(config_path if config_path.exists() else None, bridge_root=root)
    root = trinity_bridge.config_bridge_root(config, base=Path.cwd())
    trinity_bridge.ensure_bridge(root, config_path if config_path.exists() else None)
    ensure_arbitrator(root, config)
    return root, config_path, config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Arbitrate Trinity packets before bridge routing.")
    parser.add_argument("--root", default=None, help="Bridge root. Defaults to _MODEL_TRINITY/bridge.")
    parser.add_argument("--config", default=None, help="Config path. Defaults to <root>/trinity-bridge.config.json.")
    parser.add_argument("--init", action="store_true", help="Create arbitration folders and capability manifest.")
    parser.add_argument("--once", action="store_true", help="Arbitrate pending outbox packets once.")
    parser.add_argument("--watch", action="store_true", help="Run arbitration in the foreground until interrupted.")
    parser.add_argument("--max-iterations", type=int, default=0, help="Limit watch iterations; 0 means forever.")
    parser.add_argument("--dry-run", action="store_true", help="Describe arbitration without moving or writing packets.")
    parser.add_argument("--status", action="store_true", help="Print arbitration status JSON.")
    parser.add_argument("--write-capabilities", action="store_true", help="Write the default capability manifest.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root, _config_path, config = load_environment(args)

    if args.init or args.write_capabilities:
        path = write_default_capabilities(root, config)
        print(json.dumps({"event": "capabilities_written", "path": str(path)}, sort_keys=True))

    if args.once:
        for record in arbitrate_once(root, config, dry_run=args.dry_run):
            print(json.dumps(record, sort_keys=True))

    if args.watch:
        interval = float(arbitrator_config(config).get("poll_interval_seconds", config.get("poll_interval_seconds", 2.0)))
        iteration = 0
        while True:
            iteration += 1
            records = arbitrate_once(root, config, dry_run=args.dry_run)
            if records:
                for record in records:
                    print(json.dumps(record, sort_keys=True), flush=True)
            else:
                print(
                    json.dumps(
                        {"event": "idle", "iteration": iteration, "created_at": trinity_bridge.utc_now()},
                        sort_keys=True,
                    ),
                    flush=True,
                )
            if args.max_iterations and iteration >= args.max_iterations:
                break
            time.sleep(interval)

    if args.status:
        print(json.dumps(status(root, config), indent=2, sort_keys=True))

    if not any((args.init, args.write_capabilities, args.once, args.watch, args.status)):
        build_parser().print_help()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ArbitrationError, trinity_bridge.BridgeError, trinity_executor.ExecutorError) as exc:
        print(json.dumps({"schema": "digivichi.trinity.arbitration-error.v0", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)

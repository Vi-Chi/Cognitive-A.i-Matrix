"""Local file-backed Trinity bridge for Codex, Claude, and Antigravity.

The bridge routes serialized handoff packets from each agent's outbox to the
target agents' inboxes. It never executes packet contents, calls models, starts
services, installs tools, or writes outside the configured bridge root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


AGENTS = ("codex", "claude", "antigravity")
SCHEMA = "digivichi.trinity.handoff.v0"
LEDGER_SCHEMA = "digivichi.trinity.bridge-ledger.v0"
DEFAULT_BRIDGE_ROOT = Path("_MODEL_TRINITY") / "bridge"
DEFAULT_CONFIG = DEFAULT_BRIDGE_ROOT / "trinity-bridge.config.json"
DEFAULT_LEDGER = Path("ledger") / "route-ledger.jsonl"
DEFAULT_PACKET_TTL_SECONDS = 86400
MAX_PAYLOAD_BYTES = 500000
ACTION_LIKE_KINDS = {"action_request", "permission_request", "tool_request", "service_write_request"}


class BridgeError(Exception):
    """Raised for validation or bridge setup failures."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


class InterprocessLock:
    """A blocking file lock context manager."""
    def __init__(self, target_path: Path | str, *, timeout: float = 10.0, retry_ms: float = 10.0) -> None:
        self.target_path = Path(target_path)
        self.lock_path = self.target_path.with_name(self.target_path.name + ".lock")
        self.timeout = timeout
        self.retry_ms = retry_ms
        self._fd = None

    def __enter__(self) -> InterprocessLock:
        import os
        start = time.monotonic()
        while True:
            try:
                self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return self
            except FileExistsError:
                if time.monotonic() - start > self.timeout:
                    raise TimeoutError(f"Failed to acquire lock for {self.target_path} within {self.timeout}s")
                time.sleep(self.retry_ms / 1000.0)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        import os
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
            try:
                self.lock_path.unlink(missing_ok=True)
            except Exception:
                pass


def resolve_root(value: str | Path | None, *, base: Path | None = None) -> Path:
    raw = Path(value) if value else DEFAULT_BRIDGE_ROOT
    if raw.is_absolute():
        return raw
    return (base or Path.cwd()).resolve() / raw


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with InterprocessLock(path):
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    if path.exists() and path.stat().st_size > MAX_PAYLOAD_BYTES:
        raise BridgeError(f"Payload too large for bounded validation. Size exceeds {MAX_PAYLOAD_BYTES} bytes.")
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BridgeError(f"invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise BridgeError("packet must be a JSON object")
    return parsed


def default_config(root: Path) -> dict[str, Any]:
    return {
        "schema": "digivichi.trinity.bridge-config.v0",
        "bridge_root": str(root),
        "agents": list(AGENTS),
        "poll_interval_seconds": 2.0,
        "max_body_chars": 12000,
        "packet_ttl_seconds": 3600,
        "ledger_path": str(DEFAULT_LEDGER),
        "route_defaults": {
            "to": "all_except_source",
            "requires_user_approval_for_action_like_kinds": True,
        },
        "arbitrator": {
            "enabled": True,
            "ledger_path": "ledger/arbitration-ledger.jsonl",
            "latest_state_path": "state/latest-arbitration.json",
            "claims_dir": "claims",
            "compact_dir": "state/compact-handoffs",
            "capabilities_path": "agent-capabilities.json",
            "claim_ttl_seconds": 3600,
            "max_compact_chars": 1200,
            "poll_interval_seconds": 2.0,
        },
        "safety": {
            "execute_packet_contents": False,
            "allow_external_network": False,
            "allow_mcp_writes": False,
            "allow_service_connector_writes": False,
            "allow_hidden_background_agents": False,
        },
    }


def load_config(config_path: Path | None, *, bridge_root: Path | None = None) -> dict[str, Any]:
    if config_path and config_path.exists():
        config = load_json(config_path)
    else:
        root = bridge_root or DEFAULT_BRIDGE_ROOT
        config = default_config(root)
    if "bridge_root" not in config:
        config["bridge_root"] = str(bridge_root or DEFAULT_BRIDGE_ROOT)
    return config


def config_bridge_root(config: dict[str, Any], *, base: Path | None = None) -> Path:
    return resolve_root(config.get("bridge_root"), base=base)


def ensure_bridge(root: Path, config_path: Path | None = None) -> dict[str, Any]:
    for role in AGENTS:
        for bucket in ("inbox", "outbox", "processed", "rejected", "acks", "quota", "handoffs"):
            (root / bucket / role).mkdir(parents=True, exist_ok=True)
        (root / "health" / role).mkdir(parents=True, exist_ok=True)
    for bucket in ("state", "ledger", "samples", "acks", "quota", "handoffs"):
        (root / bucket).mkdir(parents=True, exist_ok=True)
    (root / "health").mkdir(parents=True, exist_ok=True)
    config = default_config(root)
    if config_path:
        if config_path.exists():
            config = load_json(config_path)
        else:
            atomic_write_json(config_path, config)
    return config


def normalize_targets(raw: Any, source: str) -> list[str]:
    if raw in (None, "", "all", ["all"]):
        return [agent for agent in AGENTS if agent != source]
    if raw == "all_except_source":
        return [agent for agent in AGENTS if agent != source]
    if isinstance(raw, str):
        targets = [part.strip().lower() for part in raw.split(",") if part.strip()]
    elif isinstance(raw, list):
        targets = [str(part).strip().lower() for part in raw if str(part).strip()]
    else:
        raise BridgeError("to must be a string, list, or all")
    if not targets:
        raise BridgeError("at least one target is required")
    unknown = [target for target in targets if target not in AGENTS]
    if unknown:
        raise BridgeError(f"unknown target(s): {', '.join(unknown)}")
    if source in targets:
        targets = [target for target in targets if target != source]
    if not targets:
        raise BridgeError("target list only contains source")
    return targets


def packet_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def parse_utc_datetime(value: Any, *, field: str = "created_at") -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise BridgeError(f"invalid {field}: missing timestamp")
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BridgeError(f"invalid {field}: {text}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def packet_ttl_seconds(packet: dict[str, Any]) -> int:
    raw = packet.get("ttl_seconds", DEFAULT_PACKET_TTL_SECONDS)
    try:
        ttl_seconds = int(raw)
    except (TypeError, ValueError) as exc:
        raise BridgeError("ttl_seconds must be an integer") from exc
    if ttl_seconds < 0:
        raise BridgeError("ttl_seconds must be non-negative")
    return ttl_seconds


def enforce_packet_ttl(packet: dict[str, Any], *, now: datetime | None = None) -> None:
    created_at = parse_utc_datetime(packet.get("created_at"))
    ttl_seconds = packet_ttl_seconds(packet)
    current = now or datetime.now(timezone.utc)
    age_seconds = int((current - created_at).total_seconds())
    if age_seconds > ttl_seconds:
        raise BridgeError(f"ttl_expired: packet age {age_seconds}s exceeds ttl_seconds={ttl_seconds}")


@contextmanager
def bridge_lock(root: Path):
    lock_path = root / ".bridge.lock"
    lock_id = uuid.uuid4().hex
    payload = {
        "schema": "digivichi.trinity.bridge-lock.v0",
        "created_at": utc_now(),
        "pid": os.getpid(),
        "lock_id": lock_id,
    }
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise BridgeError(f"bridge lock already exists: {lock_path}") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        yield lock_path
    finally:
        try:
            current = json.loads(lock_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            current = None
        if isinstance(current, dict) and current.get("lock_id") == lock_id:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def validate_packet(packet: dict[str, Any], *, source_hint: str, config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    normalized = dict(packet)
    warnings: list[str] = []
    source_hint = source_hint.lower()
    if source_hint not in AGENTS:
        raise BridgeError(f"unknown source: {source_hint}")
    normalized.setdefault("schema", SCHEMA)
    if normalized["schema"] != SCHEMA:
        raise BridgeError(f"unsupported schema: {normalized['schema']}")

    source = str(normalized.get("from") or source_hint).lower()
    if source not in AGENTS:
        raise BridgeError(f"unknown source: {source}")
    if source != source_hint:
        raise BridgeError(f"source field {source!r} differs from outbox {source_hint!r}")
    normalized["from"] = source_hint

    targets = normalize_targets(normalized.get("to"), source)
    normalized["to"] = targets

    kind = str(normalized.get("kind") or "handoff").lower()
    normalized["kind"] = kind
    normalized.setdefault("handoff_id", stable_id("handoff"))
    normalized.setdefault("created_at", utc_now())
    normalized.setdefault("ttl_seconds", DEFAULT_PACKET_TTL_SECONDS)
    normalized["ttl_seconds"] = packet_ttl_seconds(normalized)
    normalized.setdefault("priority", "MEDIUM")
    normalized.setdefault("status", "ROUTED")
    normalized.setdefault("requires_user_approval", False)
    normalized.setdefault("approval_required", normalized["requires_user_approval"])
    normalized.setdefault("constraints", [])

    # TTL Enforcement
    ttl = float(config.get("packet_ttl_seconds", 3600.0))
    created_at = normalized["created_at"]
    try:
        created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - created_dt).total_seconds()
        if age > ttl:
            raise BridgeError(f"packet expired: age {age:.1f}s exceeds TTL {ttl:.1f}s")
    except ValueError:
        pass  # skip if created_at is malformed (should be caught elsewhere)

    normalized.setdefault("files_in_scope", [])
    normalized.setdefault("known_failures", [])
    normalized.setdefault("forbidden_actions", [])
    normalized.setdefault("evidence_refs", [])

    if kind in ACTION_LIKE_KINDS and not bool(normalized.get("requires_user_approval")):
        raise BridgeError(f"{kind} requires requires_user_approval=true")

    objective = str(normalized.get("objective") or "").strip()
    summary = str(normalized.get("summary") or "").strip()
    body = str(normalized.get("body") or "").strip()
    if not (objective or summary or body):
        raise BridgeError("packet must include objective, summary, or body")

    max_body_chars = int(config.get("max_body_chars", 12000))
    if len(body) > max_body_chars:
        raise BridgeError(f"body exceeds max_body_chars={max_body_chars}")

    normalized["bridge"] = {
        "routed_at": utc_now(),
        "routing_mode": "file_relay",
        "executes_contents": False,
        "packet_sha256": packet_hash(normalized),
    }
    return normalized, warnings


def routed_name(packet: dict[str, Any], target: str) -> str:
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(packet["handoff_id"]))
    return f"{packet['bridge']['routed_at'].replace(':', '').replace('-', '')}_{safe_id}_to_{target}.json"


def move_with_collision(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    candidate = dst
    if candidate.exists():
        candidate = dst.with_name(f"{dst.stem}_{uuid.uuid4().hex[:8]}{dst.suffix}")
    shutil.move(str(src), str(candidate))
    return candidate


def reject_packet(path: Path, *, reason: str, source: str, root: Path, ledger: Path) -> dict[str, Any]:
    rejected = move_with_collision(path, root / "rejected" / source / path.name)
    reason_path = rejected.with_suffix(rejected.suffix + ".reason.txt")
    reason_path.write_text(reason + "\n", encoding="utf-8")
    event = {
        "schema": LEDGER_SCHEMA,
        "event": "rejected",
        "source": source,
        "path": str(path),
        "rejected_path": str(rejected),
        "reason": reason,
        "created_at": utc_now(),
    }
    append_jsonl(ledger, event)
    return event


def check_quota(root: Path, target: str) -> bool:
    quota_path = root / "quota" / target / "quota_state.json"
    if quota_path.exists():
        try:
            state = load_json(quota_path)
            if state.get("status") == "quota_limited":
                return False
        except BridgeError:
            pass
    return True


def route_packet(path: Path, *, source: str, root: Path, config: dict[str, Any], ledger: Path, dry_run: bool = False) -> dict[str, Any]:
    try:
        packet = load_json(path)
        normalized, warnings = validate_packet(packet, source_hint=source, config=config)
        enforce_packet_ttl(normalized)
        
        for target in normalized["to"]:
            if not check_quota(root, target):
                raise BridgeError(f"Target {target} is quota_limited. Heavy routing blocked.")
    except BridgeError as exc:
        if dry_run:
            return {
                "schema": LEDGER_SCHEMA,
                "event": "would_reject",
                "source": source,
                "path": str(path),
                "reason": str(exc),
                "created_at": utc_now(),
            }
        return reject_packet(path, reason=str(exc), source=source, root=root, ledger=ledger)

    deliveries = []
    for target in normalized["to"]:
        destination = root / "inbox" / target / routed_name(normalized, target)
        deliveries.append(str(destination))
        if not dry_run:
            atomic_write_json(destination, normalized)

    processed = root / "processed" / source / path.name
    if not dry_run:
        processed = move_with_collision(path, processed)

    event = {
        "schema": LEDGER_SCHEMA,
        "event": "routed" if not dry_run else "would_route",
        "handoff_id": normalized["handoff_id"],
        "source": source,
        "targets": normalized["to"],
        "source_path": str(path),
        "processed_path": str(processed),
        "deliveries": deliveries,
        "warnings": warnings,
        "created_at": utc_now(),
    }
    if not dry_run:
        append_jsonl(ledger, event)
    return event


def iter_outbox_packets(root: Path) -> Iterable[tuple[str, Path]]:
    for source in AGENTS:
        outbox = root / "outbox" / source
        if not outbox.exists():
            continue
        for path in sorted(outbox.glob("*.json")):
            if path.name.startswith("."):
                continue
            yield source, path


def route_once(root: Path, config: dict[str, Any], *, dry_run: bool = False) -> list[dict[str, Any]]:
    ledger = root / Path(config.get("ledger_path", str(DEFAULT_LEDGER)))
    events = []
    packets = list(iter_outbox_packets(root))
    if dry_run:
        for source, path in packets:
            events.append(route_packet(path, source=source, root=root, config=config, ledger=ledger, dry_run=True))
        return events
    if not packets:
        return events
    with bridge_lock(root):
        for source, path in packets:
            events.append(route_packet(path, source=source, root=root, config=config, ledger=ledger, dry_run=False))
    return events


def make_packet(args: argparse.Namespace) -> dict[str, Any]:
    targets = args.to or "all_except_source"
    return {
        "schema": SCHEMA,
        "handoff_id": args.handoff_id or stable_id("handoff"),
        "created_at": utc_now(),
        "from": args.from_agent,
        "to": targets,
        "kind": args.kind,
        "priority": args.priority,
        "requires_user_approval": args.requires_user_approval,
        "mode": args.mode,
        "objective": args.objective,
        "summary": args.summary or args.objective,
        "body": args.body,
        "files_in_scope": args.files_in_scope or [],
        "constraints": args.constraints or [],
        "known_failures": args.known_failures or [],
        "forbidden_actions": args.forbidden_actions or [],
        "evidence_refs": args.evidence_refs or [],
        "requested_output": args.requested_output,
        "reply_to": args.reply_to,
        "status": "DRAFT",
    }


def post_packet(root: Path, packet: dict[str, Any]) -> Path:
    source = str(packet["from"]).lower()
    if source not in AGENTS:
        raise BridgeError(f"unknown source: {source}")
    outbox = root / "outbox" / source
    outbox.mkdir(parents=True, exist_ok=True)
    filename = f"{packet['handoff_id']}.json"
    path = outbox / filename
    atomic_write_json(path, packet)
    return path


def status(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, Any] = {
        "schema": "digivichi.trinity.bridge-status.v0",
        "created_at": utc_now(),
        "root": str(root),
        "outbox": {},
        "inbox": {},
        "processed": {},
        "rejected": {},
    }
    for bucket in ("outbox", "inbox", "processed", "rejected"):
        for role in AGENTS:
            folder = root / bucket / role
            counts[bucket][role] = len(list(folder.glob("*.json"))) if folder.exists() else 0
    ledger = root / Path(config.get("ledger_path", str(DEFAULT_LEDGER)))
    counts["ledger_exists"] = ledger.exists()
    counts["ledger_path"] = str(ledger)
    return counts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Trinity bridge for Codex, Claude, and Antigravity.")
    parser.add_argument("--root", default=None, help="Bridge root. Defaults to _MODEL_TRINITY/bridge.")
    parser.add_argument("--config", default=None, help="Config path. Defaults to <root>/trinity-bridge.config.json.")
    parser.add_argument("--init", action="store_true", help="Create bridge directories and default config.")
    parser.add_argument("--once", action="store_true", help="Route all pending outbox packets once.")
    parser.add_argument("--watch", action="store_true", help="Poll and route pending packets until interrupted.")
    parser.add_argument("--max-iterations", type=int, default=0, help="Limit watch iterations; 0 means forever.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and describe routes without writing deliveries.")
    parser.add_argument("--status", action="store_true", help="Print bridge status JSON.")
    parser.add_argument("--post", action="store_true", help="Write a new packet to the source outbox.")
    parser.add_argument("--route-now", action="store_true", help="Route immediately after --post.")
    parser.add_argument("--from", dest="from_agent", choices=AGENTS, default="codex")
    parser.add_argument("--to", default=None, help="Comma-separated targets, 'all', or omit for all except source.")
    parser.add_argument("--kind", default="handoff")
    parser.add_argument("--priority", choices=("LOW", "MEDIUM", "HIGH", "CRITICAL"), default="MEDIUM")
    parser.add_argument("--mode", default="review")
    parser.add_argument("--objective", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--body", default="")
    parser.add_argument("--requested-output", default="HandoffNote")
    parser.add_argument("--requires-user-approval", action="store_true")
    parser.add_argument("--handoff-id", default=None)
    parser.add_argument("--reply-to", default=None)
    parser.add_argument("--files-in-scope", action="append")
    parser.add_argument("--constraints", action="append")
    parser.add_argument("--known-failures", action="append")
    parser.add_argument("--forbidden-actions", action="append")
    parser.add_argument("--evidence-refs", action="append")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = resolve_root(args.root)
    config_path = Path(args.config).resolve() if args.config else root / "trinity-bridge.config.json"

    if args.init:
        config = ensure_bridge(root, config_path)
    else:
        config = load_config(config_path if config_path.exists() else None, bridge_root=root)
        root = config_bridge_root(config, base=Path.cwd())
        ensure_bridge(root, config_path if config_path.exists() else None)

    if args.post:
        packet = make_packet(args)
        path = post_packet(root, packet)
        print(json.dumps({"event": "posted", "path": str(path), "handoff_id": packet["handoff_id"]}, sort_keys=True))

    if args.once or args.route_now:
        for event in route_once(root, config, dry_run=args.dry_run):
            print(json.dumps(event, sort_keys=True))

    if args.watch:
        print("Error: --watch chat-polling is disabled for safety. Use --once.", file=sys.stderr)
        return 1

    if args.status:
        print(json.dumps(status(root, config), indent=2, sort_keys=True))

    if not any((args.init, args.post, args.once, args.route_now, args.watch, args.status)):
        build_parser().print_help()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BridgeError as exc:
        print(json.dumps({"schema": "digivichi.trinity.bridge-error.v0", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)

"""Allowlisted local executor for Trinity bridge execution requests.

The executor consumes structured execution_request packets from Codex's bridge
inbox and runs only hardcoded deterministic local tasks. It does not interpret
free-form prose as commands, does not use shell=True, does not call models, and
does not write outside the configured bridge/report locations.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

try:
    import trinity_bridge
except ImportError:  # pragma: no cover - defensive when imported from tests
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import trinity_bridge  # type: ignore


EXECUTOR_ROLE = "codex"
REQUEST_KIND = "execution_request"
RESULT_KIND = "execution_result"
REQUEST_SCHEMA = "digivichi.trinity.execution-request.v0"
RESULT_SCHEMA = "digivichi.trinity.execution-result.v0"
LEDGER_SCHEMA = "digivichi.trinity.execution-ledger.v0"
DEFAULT_EXECUTION_LEDGER = Path("ledger") / "execution-ledger.jsonl"
DEFAULT_STDOUT_LIMIT = 6000
DEFAULT_STDERR_LIMIT = 4000

TOKEN_RE = re.compile(r"\b(?:sk|pk|ghp|github_pat|xoxb|xoxp)-[A-Za-z0-9_=-]{16,}\b")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password|credential)\b\s*[:=]\s*([\"']?)[^\s,\"']+"
)


class ExecutorError(Exception):
    """Raised when a packet cannot be safely executed."""


@dataclass(frozen=True)
class ExecutorContext:
    repo_root: Path
    bridge_root: Path
    config: dict[str, Any]
    max_stdout_chars: int = DEFAULT_STDOUT_LIMIT
    max_stderr_chars: int = DEFAULT_STDERR_LIMIT


@dataclass(frozen=True)
class TaskDefinition:
    task_id: str
    description: str
    runner: Callable[[ExecutorContext, dict[str, Any]], dict[str, Any]]
    timeout_seconds: int = 30
    requires_user_approval: bool = False
    mutates_repo_files: bool = False


def redact_sensitive(text: str | bytes | None) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    redacted = TOKEN_RE.sub("<REDACTED_TOKEN>", text)
    return SECRET_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=<REDACTED>", redacted)


def trim(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    omitted = len(text) - limit
    return f"{text[:limit]}\n...[truncated {omitted} chars]"


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def executor_config(config: dict[str, Any]) -> dict[str, Any]:
    raw = config.get("executor")
    return raw if isinstance(raw, dict) else {}


def execution_ledger_path(root: Path, config: dict[str, Any]) -> Path:
    configured = executor_config(config).get("ledger_path", str(DEFAULT_EXECUTION_LEDGER))
    return root / Path(str(configured))


def output_limits(config: dict[str, Any]) -> tuple[int, int]:
    raw = executor_config(config)
    stdout_limit = int(raw.get("max_stdout_chars", DEFAULT_STDOUT_LIMIT))
    stderr_limit = int(raw.get("max_stderr_chars", DEFAULT_STDERR_LIMIT))
    return stdout_limit, stderr_limit


def ensure_executor(root: Path) -> None:
    for bucket in ("executed", "execution_rejected"):
        (root / bucket / EXECUTOR_ROLE).mkdir(parents=True, exist_ok=True)
    (root / "ledger").mkdir(parents=True, exist_ok=True)


def run_subprocess_task(
    context: ExecutorContext,
    command: list[str],
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    started = time.monotonic()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(context.repo_root)
    try:
        completed = subprocess.run(
            command,
            cwd=str(context.repo_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
        stdout = trim(redact_sensitive(completed.stdout), context.max_stdout_chars)
        stderr = trim(redact_sensitive(completed.stderr), context.max_stderr_chars)
        return {
            "status": "SUCCEEDED" if completed.returncode == 0 else "FAILED",
            "exit_code": completed.returncode,
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "duration_seconds": round(time.monotonic() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "FAILED",
            "exit_code": 124,
            "command": command,
            "stdout": trim(redact_sensitive(exc.stdout), context.max_stdout_chars),
            "stderr": trim(redact_sensitive(exc.stderr), context.max_stderr_chars),
            "duration_seconds": round(time.monotonic() - started, 3),
            "error": f"timeout after {timeout_seconds}s",
        }


def task_bridge_status(context: ExecutorContext, args: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    report = trinity_bridge.status(context.bridge_root, context.config)
    return {
        "status": "SUCCEEDED",
        "exit_code": 0,
        "stdout": json.dumps(report, indent=2, sort_keys=True),
        "stderr": "",
        "duration_seconds": round(time.monotonic() - started, 3),
        "records": report,
    }


def task_bridge_route_once_dry_run(context: ExecutorContext, args: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    events = trinity_bridge.route_once(context.bridge_root, context.config, dry_run=True)
    return {
        "status": "SUCCEEDED",
        "exit_code": 0,
        "stdout": json.dumps(events, indent=2, sort_keys=True),
        "stderr": "",
        "duration_seconds": round(time.monotonic() - started, 3),
        "records": {"would_route_count": len(events), "events": events},
    }


def task_doc_inventory(context: ExecutorContext, args: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    root = context.repo_root
    trinity_root = root / "_MODEL_TRINITY"
    kb_root = root / "_PROJECT_KNOWLEDGE_BASE"
    inventory = {
        "root_docs": [
            name
            for name in ("DO_ANYTHING_NOW.md", "AGENTS.md", "CLAUDE.md", "ANTIGRAVITY.md", "README.md")
            if (root / name).exists()
        ],
        "trinity_docs": sorted(path.name for path in trinity_root.glob("*.md")) if trinity_root.exists() else [],
        "bridge_docs": sorted(path.name for path in (trinity_root / "bridge").glob("*.md"))
        if (trinity_root / "bridge").exists()
        else [],
        "kb_front_door": [
            name
            for name in ("README.md", "AXIOMS_OF_OMNI.md", "GLOSSARY.md", "STATE_OF_SYSTEM_2026-06-12.md")
            if (kb_root / name).exists()
        ],
        "trinity_tests": sorted(path.name for path in (root / "ai_chi" / "tests").glob("test_trinity*.py")),
        "scripts": sorted(path.name for path in (root / "scripts").glob("trinity_*.py")),
    }
    return {
        "status": "SUCCEEDED",
        "exit_code": 0,
        "stdout": json.dumps(inventory, indent=2, sort_keys=True),
        "stderr": "",
        "duration_seconds": round(time.monotonic() - started, 3),
        "records": inventory,
    }


def task_axioms_floor(context: ExecutorContext, args: dict[str, Any]) -> dict[str, Any]:
    return run_subprocess_task(
        context,
        [sys.executable, "-c", "from ai_chi.core.axioms import verify_floor; print(verify_floor())"],
        timeout_seconds=20,
    )


def task_trinity_bridge_tests(context: ExecutorContext, args: dict[str, Any]) -> dict[str, Any]:
    return run_subprocess_task(
        context,
        [sys.executable, "-m", "unittest", "ai_chi.tests.test_trinity_bridge", "-q"],
        timeout_seconds=60,
    )


def task_trinity_executor_tests(context: ExecutorContext, args: dict[str, Any]) -> dict[str, Any]:
    return run_subprocess_task(
        context,
        [sys.executable, "-m", "unittest", "ai_chi.tests.test_trinity_executor", "-q"],
        timeout_seconds=60,
    )


def task_trinity_arbitrator_tests(context: ExecutorContext, args: dict[str, Any]) -> dict[str, Any]:
    return run_subprocess_task(
        context,
        [sys.executable, "-m", "unittest", "ai_chi.tests.test_trinity_arbitrator", "-q"],
        timeout_seconds=60,
    )


def task_trinity_cycle_tests(context: ExecutorContext, args: dict[str, Any]) -> dict[str, Any]:
    return run_subprocess_task(
        context,
        [sys.executable, "-m", "unittest", "ai_chi.tests.test_trinity_dan_cycle", "-q"],
        timeout_seconds=60,
    )


def task_trinity_tests(context: ExecutorContext, args: dict[str, Any]) -> dict[str, Any]:
    return run_subprocess_task(
        context,
        [
            sys.executable,
            "-m",
            "unittest",
            "ai_chi.tests.test_trinity_bridge",
            "ai_chi.tests.test_trinity_executor",
            "ai_chi.tests.test_trinity_arbitrator",
            "ai_chi.tests.test_trinity_dan_cycle",
            "-q",
        ],
        timeout_seconds=90,
    )


def task_full_ai_chi_tests(context: ExecutorContext, args: dict[str, Any]) -> dict[str, Any]:
    return run_subprocess_task(
        context,
        [sys.executable, "-m", "unittest", "discover", "-s", "ai_chi/tests", "-q"],
        timeout_seconds=180,
    )


TASKS: dict[str, TaskDefinition] = {
    "bridge_status": TaskDefinition("bridge_status", "Report Trinity bridge queue counts.", task_bridge_status),
    "bridge_route_once_dry_run": TaskDefinition(
        "bridge_route_once_dry_run",
        "Validate pending bridge outbox routes without moving packets.",
        task_bridge_route_once_dry_run,
    ),
    "doc_inventory": TaskDefinition(
        "doc_inventory",
        "Return a compact inventory of root, Trinity, bridge, and KB front-door docs.",
        task_doc_inventory,
    ),
    "axioms_floor": TaskDefinition(
        "axioms_floor",
        "Run the Axioms floor verification.",
        task_axioms_floor,
        timeout_seconds=20,
    ),
    "trinity_bridge_tests": TaskDefinition(
        "trinity_bridge_tests",
        "Run Trinity bridge unit tests only.",
        task_trinity_bridge_tests,
        timeout_seconds=60,
    ),
    "trinity_executor_tests": TaskDefinition(
        "trinity_executor_tests",
        "Run Trinity executor unit tests only.",
        task_trinity_executor_tests,
        timeout_seconds=60,
    ),
    "trinity_arbitrator_tests": TaskDefinition(
        "trinity_arbitrator_tests",
        "Run Trinity arbitrator unit tests only.",
        task_trinity_arbitrator_tests,
        timeout_seconds=60,
    ),
    "trinity_cycle_tests": TaskDefinition(
        "trinity_cycle_tests",
        "Run Trinity+DAN cycle unit tests only.",
        task_trinity_cycle_tests,
        timeout_seconds=60,
    ),
    "trinity_tests": TaskDefinition(
        "trinity_tests",
        "Run Trinity bridge, executor, arbitrator, and cycle unit tests.",
        task_trinity_tests,
        timeout_seconds=90,
    ),
    "full_ai_chi_tests": TaskDefinition(
        "full_ai_chi_tests",
        "Run the full ai_chi unittest discovery suite.",
        task_full_ai_chi_tests,
        timeout_seconds=180,
    ),
}


def task_catalog() -> list[dict[str, Any]]:
    return [
        {
            "task_id": task.task_id,
            "description": task.description,
            "timeout_seconds": task.timeout_seconds,
            "requires_user_approval": task.requires_user_approval,
            "mutates_repo_files": task.mutates_repo_files,
        }
        for task in TASKS.values()
    ]


def iter_codex_inbox(root: Path) -> Iterable[Path]:
    inbox = root / "inbox" / EXECUTOR_ROLE
    if not inbox.exists():
        return
    for path in sorted(inbox.glob("*.json")):
        if not path.name.startswith("."):
            yield path


def is_execution_request(packet: dict[str, Any]) -> bool:
    return str(packet.get("kind") or "").lower() == REQUEST_KIND


def load_execution(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    packet = trinity_bridge.load_json(path)
    if not is_execution_request(packet):
        raise ExecutorError("not an execution_request")
    execution = packet.get("execution")
    if not isinstance(execution, dict):
        raise ExecutorError("execution_request requires structured execution object")
    if execution.get("schema", REQUEST_SCHEMA) != REQUEST_SCHEMA:
        raise ExecutorError(f"unsupported execution schema: {execution.get('schema')}")
    return packet, execution


def validate_execution(packet: dict[str, Any], execution: dict[str, Any]) -> TaskDefinition:
    source = str(packet.get("from") or "").lower()
    if source not in trinity_bridge.AGENTS:
        raise ExecutorError(f"unknown source: {source or '<missing>'}")
    targets = packet.get("to", [])
    if isinstance(targets, str):
        targets = [targets]
    if EXECUTOR_ROLE not in [str(target).lower() for target in targets]:
        raise ExecutorError("execution_request is not addressed to codex")
    if bool(packet.get("requires_user_approval") or packet.get("approval_required")):
        raise ExecutorError("approval-required packets are not auto-executed")
    task_id = str(execution.get("task_id") or "").strip()
    if not task_id:
        raise ExecutorError("execution.task_id is required")
    task = TASKS.get(task_id)
    if task is None:
        raise ExecutorError(f"unknown execution.task_id: {task_id}")
    if task.requires_user_approval or bool(execution.get("requires_user_approval")):
        raise ExecutorError(f"{task_id} requires user approval and is not auto-executed")
    args = execution.get("args", {})
    if args is not None and not isinstance(args, dict):
        raise ExecutorError("execution.args must be an object when present")
    try:
        result_targets(packet, execution)
    except trinity_bridge.BridgeError as exc:
        raise ExecutorError(f"invalid execution.result_to: {exc}") from exc
    return task


def result_targets(packet: dict[str, Any], execution: dict[str, Any]) -> list[str]:
    requested = execution.get("result_to")
    source = str(packet.get("from") or "").lower()
    raw_targets = requested if requested is not None else (source if source != EXECUTOR_ROLE else "all_except_source")
    return trinity_bridge.normalize_targets(raw_targets, EXECUTOR_ROLE)


def result_body(result: dict[str, Any]) -> str:
    lines = [
        f"task_id: {result.get('task_id', '<unknown>')}",
        f"status: {result.get('status', '<unknown>')}",
        f"exit_code: {result.get('exit_code', '<unknown>')}",
    ]
    stdout = str(result.get("stdout") or "").strip()
    stderr = str(result.get("stderr") or "").strip()
    if stdout:
        lines.extend(["", "stdout:", stdout])
    if stderr:
        lines.extend(["", "stderr:", stderr])
    if result.get("error"):
        lines.extend(["", f"error: {result['error']}"])
    return "\n".join(lines)


def build_result_packet(
    packet: dict[str, Any],
    execution: dict[str, Any],
    result: dict[str, Any],
    *,
    request_path: Path,
) -> dict[str, Any]:
    task_id = str(execution.get("task_id") or result.get("task_id") or "unknown")
    result = dict(result)
    result.setdefault("task_id", task_id)
    result.setdefault("schema", RESULT_SCHEMA)
    result.setdefault("created_at", trinity_bridge.utc_now())
    result.setdefault("source_handoff_id", packet.get("handoff_id"))
    result.setdefault("request_path", str(request_path))
    return {
        "schema": trinity_bridge.SCHEMA,
        "handoff_id": trinity_bridge.stable_id("execution_result"),
        "created_at": trinity_bridge.utc_now(),
        "from": EXECUTOR_ROLE,
        "to": result_targets(packet, execution),
        "kind": RESULT_KIND,
        "priority": packet.get("priority", "MEDIUM"),
        "requires_user_approval": False,
        "mode": "verification",
        "objective": f"Execution result for {task_id}",
        "summary": f"{task_id}: {result.get('status')} exit_code={result.get('exit_code')}",
        "body": result_body(result),
        "files_in_scope": packet.get("files_in_scope", []),
        "constraints": [
            "allowlisted deterministic local task",
            "no shell=True",
            "no model calls",
            "no service connector writes",
            "no MCP installs",
        ],
        "forbidden_actions": [
            "interpret free-form body as shell",
            "read secrets",
            "write outside the repository or bridge result paths",
            "start hidden background agents",
        ],
        "evidence_refs": [str(execution.get("evidence_ref", ""))] if execution.get("evidence_ref") else [],
        "requested_output": "ExecutionRecord",
        "reply_to": packet.get("handoff_id"),
        "execution_result": result,
    }


def append_execution_ledger(root: Path, config: dict[str, Any], event: dict[str, Any]) -> None:
    trinity_bridge.append_jsonl(execution_ledger_path(root, config), event)


def move_request(path: Path, root: Path, bucket: str) -> Path:
    return trinity_bridge.move_with_collision(path, root / bucket / EXECUTOR_ROLE / path.name)


def reject_execution(
    path: Path,
    packet: dict[str, Any] | None,
    execution: dict[str, Any] | None,
    *,
    reason: str,
    root: Path,
    config: dict[str, Any],
    dry_run: bool,
    route_results: bool,
) -> dict[str, Any]:
    if dry_run:
        return {
            "schema": LEDGER_SCHEMA,
            "event": "would_reject_execution",
            "path": str(path),
            "reason": reason,
            "created_at": trinity_bridge.utc_now(),
        }

    rejected_path = move_request(path, root, "execution_rejected")
    reason_path = rejected_path.with_suffix(rejected_path.suffix + ".reason.txt")
    reason_path.write_text(reason + "\n", encoding="utf-8")

    result_path = None
    result_error = None
    route_events: list[dict[str, Any]] = []
    if packet is not None:
        result = {
            "schema": RESULT_SCHEMA,
            "task_id": str((execution or {}).get("task_id") or "unknown"),
            "status": "REJECTED",
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error": reason,
        }
        try:
            result_packet = build_result_packet(packet, execution or {}, result, request_path=path)
            result_path = trinity_bridge.post_packet(root, result_packet)
            if route_results:
                route_events = trinity_bridge.route_once(root, config)
        except (ExecutorError, trinity_bridge.BridgeError) as exc:
            result_error = str(exc)

    event = {
        "schema": LEDGER_SCHEMA,
        "event": "execution_rejected",
        "path": str(path),
        "rejected_path": str(rejected_path),
        "result_path": str(result_path) if result_path else None,
        "result_error": result_error,
        "route_events": route_events,
        "reason": reason,
        "created_at": trinity_bridge.utc_now(),
    }
    append_execution_ledger(root, config, event)
    return event


def execute_request(
    path: Path,
    *,
    context: ExecutorContext,
    dry_run: bool = False,
    route_results: bool = False,
) -> dict[str, Any] | None:
    try:
        packet = trinity_bridge.load_json(path)
    except trinity_bridge.BridgeError as exc:
        return reject_execution(
            path,
            None,
            None,
            reason=str(exc),
            root=context.bridge_root,
            config=context.config,
            dry_run=dry_run,
            route_results=route_results,
        )

    if not is_execution_request(packet):
        return None

    execution: dict[str, Any] | None = None
    try:
        packet, execution = load_execution(path)
        task = validate_execution(packet, execution)
    except (ExecutorError, trinity_bridge.BridgeError) as exc:
        return reject_execution(
            path,
            packet,
            execution,
            reason=str(exc),
            root=context.bridge_root,
            config=context.config,
            dry_run=dry_run,
            route_results=route_results,
        )

    if dry_run:
        return {
            "schema": LEDGER_SCHEMA,
            "event": "would_execute",
            "path": str(path),
            "task_id": task.task_id,
            "created_at": trinity_bridge.utc_now(),
        }

    args = execution.get("args", {}) or {}
    result = task.runner(context, args)
    result["task_id"] = task.task_id
    result["schema"] = RESULT_SCHEMA
    result["created_at"] = trinity_bridge.utc_now()

    result_packet = build_result_packet(packet, execution, result, request_path=path)
    result_path = trinity_bridge.post_packet(context.bridge_root, result_packet)
    executed_path = move_request(path, context.bridge_root, "executed")
    route_events: list[dict[str, Any]] = []
    if route_results:
        route_events = trinity_bridge.route_once(context.bridge_root, context.config)

    event = {
        "schema": LEDGER_SCHEMA,
        "event": "executed",
        "handoff_id": packet.get("handoff_id"),
        "source": packet.get("from"),
        "task_id": task.task_id,
        "status": result.get("status"),
        "exit_code": result.get("exit_code"),
        "request_path": str(path),
        "executed_path": str(executed_path),
        "result_path": str(result_path),
        "route_events": route_events,
        "created_at": trinity_bridge.utc_now(),
    }
    append_execution_ledger(context.bridge_root, context.config, event)
    return event


def process_once(
    root: Path,
    config: dict[str, Any],
    *,
    repo_root: Path | None = None,
    dry_run: bool = False,
    route_results: bool = False,
) -> list[dict[str, Any]]:
    ensure_executor(root)
    stdout_limit, stderr_limit = output_limits(config)
    context = ExecutorContext(
        repo_root=(repo_root or repo_root_from_script()).resolve(),
        bridge_root=root,
        config=config,
        max_stdout_chars=stdout_limit,
        max_stderr_chars=stderr_limit,
    )
    events: list[dict[str, Any]] = []
    for path in iter_codex_inbox(root):
        event = execute_request(path, context=context, dry_run=dry_run, route_results=route_results)
        if event is not None:
            events.append(event)
    return events


def status(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    ensure_executor(root)
    pending = 0
    for path in iter_codex_inbox(root):
        try:
            packet = trinity_bridge.load_json(path)
        except trinity_bridge.BridgeError:
            continue
        if is_execution_request(packet):
            pending += 1
    return {
        "schema": "digivichi.trinity.executor-status.v0",
        "created_at": trinity_bridge.utc_now(),
        "root": str(root),
        "executor_role": EXECUTOR_ROLE,
        "pending_execution_requests": pending,
        "executed": len(list((root / "executed" / EXECUTOR_ROLE).glob("*.json"))),
        "execution_rejected": len(list((root / "execution_rejected" / EXECUTOR_ROLE).glob("*.json"))),
        "result_outbox": len(list((root / "outbox" / EXECUTOR_ROLE).glob("*.json"))),
        "ledger_path": str(execution_ledger_path(root, config)),
        "ledger_exists": execution_ledger_path(root, config).exists(),
        "safe_tasks": task_catalog(),
    }


def load_environment(args: argparse.Namespace) -> tuple[Path, Path, dict[str, Any]]:
    root = trinity_bridge.resolve_root(args.root)
    config_path = Path(args.config).resolve() if args.config else root / "trinity-bridge.config.json"
    config = trinity_bridge.load_config(config_path if config_path.exists() else None, bridge_root=root)
    root = trinity_bridge.config_bridge_root(config, base=Path.cwd())
    trinity_bridge.ensure_bridge(root, config_path if config_path.exists() else None)
    ensure_executor(root)
    return root, config_path, config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Allowlisted Trinity execution clerk for Codex.")
    parser.add_argument("--root", default=None, help="Bridge root. Defaults to _MODEL_TRINITY/bridge.")
    parser.add_argument("--config", default=None, help="Config path. Defaults to <root>/trinity-bridge.config.json.")
    parser.add_argument("--once", action="store_true", help="Process pending Codex execution requests once.")
    parser.add_argument("--watch", action="store_true", help="Poll and process requests in the foreground.")
    parser.add_argument("--max-iterations", type=int, default=0, help="Limit watch iterations; 0 means forever.")
    parser.add_argument("--dry-run", action="store_true", help="Validate requests without executing or moving files.")
    parser.add_argument("--route-results", action="store_true", help="Route result packets after posting them.")
    parser.add_argument("--status", action="store_true", help="Print executor status JSON.")
    parser.add_argument("--list-tasks", action="store_true", help="Print the safe task catalog JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root, _config_path, config = load_environment(args)

    if args.list_tasks:
        print(json.dumps({"schema": "digivichi.trinity.safe-task-catalog.v0", "tasks": task_catalog()}, indent=2))

    if args.once:
        for event in process_once(root, config, dry_run=args.dry_run, route_results=args.route_results):
            print(json.dumps(event, sort_keys=True))

    if args.watch:
        print("Error: --watch polling is disabled for safety. Use --once.", file=sys.stderr)
        return 1

    if args.status:
        print(json.dumps(status(root, config), indent=2, sort_keys=True))

    if not any((args.list_tasks, args.once, args.watch, args.status)):
        build_parser().print_help()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ExecutorError, trinity_bridge.BridgeError) as exc:
        print(json.dumps({"schema": "digivichi.trinity.executor-error.v0", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)

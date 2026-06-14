"""Foreground Trinity + DAN cycle runner.

This script coordinates the local Trinity bridge and safe executor into one
bounded cycle. It routes handoff packets, processes allowlisted execution
requests, optionally runs deterministic DAN checks, writes ledgers, and can post
a compact summary packet. It does not install tools, call models, mutate app
configs, or run as a hidden background service.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import trinity_bridge
    import trinity_executor
    import trinity_arbitrator
except ImportError:  # pragma: no cover - defensive when imported from tests
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import trinity_bridge  # type: ignore
    import trinity_executor  # type: ignore
    import trinity_arbitrator  # type: ignore


SCHEMA = "digivichi.trinity.dan-cycle.v0"
DEFAULT_CYCLE_LEDGER = Path("ledger") / "cycle-ledger.jsonl"
DEFAULT_LATEST_STATE = Path("state") / "latest-cycle.json"
DEFAULT_HEALTH_SUMMARY = Path("health") / "health_summary.json"
DEFAULT_HEALTH_SUMMARY_MAX_AGE_SECONDS = 300
CHECK_MODES = ("none", "quick", "trinity", "full")


class CycleError(Exception):
    """Raised when the cycle runner cannot safely proceed."""


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def load_environment(args: argparse.Namespace) -> tuple[Path, Path, dict[str, Any]]:
    root = trinity_bridge.resolve_root(args.root)
    config_path = Path(args.config).resolve() if args.config else root / "trinity-bridge.config.json"
    config = trinity_bridge.load_config(config_path if config_path.exists() else None, bridge_root=root)
    root = trinity_bridge.config_bridge_root(config, base=Path.cwd())
    trinity_bridge.ensure_bridge(root, config_path if config_path.exists() else None)
    trinity_executor.ensure_executor(root)
    trinity_arbitrator.ensure_arbitrator(root, config)
    (root / "ledger").mkdir(parents=True, exist_ok=True)
    (root / "state").mkdir(parents=True, exist_ok=True)
    return root, config_path, config


def cycle_config(config: dict[str, Any]) -> dict[str, Any]:
    raw = config.get("cycle")
    return raw if isinstance(raw, dict) else {}


def utc_now_dt() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_utc(value: str) -> datetime:
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def cycle_ledger_path(root: Path, config: dict[str, Any]) -> Path:
    configured = cycle_config(config).get("ledger_path", str(DEFAULT_CYCLE_LEDGER))
    return root / Path(str(configured))


def latest_state_path(root: Path, config: dict[str, Any]) -> Path:
    configured = cycle_config(config).get("latest_state_path", str(DEFAULT_LATEST_STATE))
    return root / Path(str(configured))


def health_summary_path(root: Path, config: dict[str, Any]) -> Path:
    configured = cycle_config(config).get("health_summary_path", str(DEFAULT_HEALTH_SUMMARY))
    return root / Path(str(configured))


def conservative_liveness_routing(root: Path, config: dict[str, Any], *, reason: str) -> dict[str, Any]:
    agents = {
        agent: {
            "status": "STALE",
            "queue_only": True,
            "context_mode": "compact",
            "token_automation_weight": 0.25,
            "send_new_work": False,
            "may_auto_execute": False,
            "can_expand_authority": False,
            "reason": reason,
        }
        for agent in trinity_bridge.AGENTS
    }
    return {
        "schema": "digivichi.trinity.dan-cycle.liveness-routing.v0",
        "source_status": "CONSERVATIVE_FALLBACK",
        "reason": reason,
        "health_summary_path": str(health_summary_path(root, config)),
        "summary_age_seconds": None,
        "summary_max_age_seconds": int(
            cycle_config(config).get("health_summary_max_age_seconds", DEFAULT_HEALTH_SUMMARY_MAX_AGE_SECONDS)
        ),
        "agents": agents,
        "effect_scope": ["volume", "format", "timing"],
        "authority_boundary": {
            "alive_grants_authority": False,
            "executor_allowlist_only": True,
            "proposal_only_preserved": True,
            "gated_action_triggered_by_liveness": False,
            "capabilities_are_advisory_only": True,
        },
    }


def clamp_weight(value: Any) -> float:
    try:
        weight = float(value)
    except (TypeError, ValueError):
        return 0.1
    return max(0.0, min(1.0, weight))


def liveness_routing(root: Path, config: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    path = health_summary_path(root, config)
    if not path.exists():
        return conservative_liveness_routing(root, config, reason="health_summary_missing")
    try:
        summary = trinity_bridge.load_json(path)
        created_at = parse_utc(str(summary.get("created_at_utc", "")))
    except Exception:
        return conservative_liveness_routing(root, config, reason="health_summary_unreadable")

    current = now or utc_now_dt()
    age_seconds = max(0, int((current - created_at).total_seconds()))
    max_age = int(cycle_config(config).get("health_summary_max_age_seconds", DEFAULT_HEALTH_SUMMARY_MAX_AGE_SECONDS))
    if age_seconds > max_age:
        decision = conservative_liveness_routing(root, config, reason="health_summary_stale")
        decision["summary_age_seconds"] = age_seconds
        return decision

    agents_raw = summary.get("agents")
    if not isinstance(agents_raw, dict):
        return conservative_liveness_routing(root, config, reason="health_summary_missing_agents")
    recommendation = summary.get("routing_recommendation") if isinstance(summary.get("routing_recommendation"), dict) else {}
    queue_only_for = set(str(agent) for agent in recommendation.get("queue_only_for", []) if agent)
    compact_for = set(str(agent) for agent in recommendation.get("compact_summaries_for", []) if agent)
    send_new_work_to = set(str(agent) for agent in recommendation.get("send_new_work_to", []) if agent)
    agents: dict[str, dict[str, Any]] = {}
    for agent in trinity_bridge.AGENTS:
        raw = agents_raw.get(agent) if isinstance(agents_raw.get(agent), dict) else {}
        status = str(raw.get("status") or "UNKNOWN").upper()
        queue_only = agent in queue_only_for or status in {"UNKNOWN", "STALE", "DOWN", "PAUSED", "BLOCKED"}
        context_mode = "compact" if queue_only or agent in compact_for or status != "ALIVE" else "normal"
        agents[agent] = {
            "status": status,
            "queue_only": bool(queue_only),
            "context_mode": context_mode,
            "token_automation_weight": clamp_weight(raw.get("token_automation_weight")),
            "send_new_work": bool(agent in send_new_work_to and not queue_only),
            "may_auto_execute": False,
            "can_expand_authority": False,
            "reason": "health_summary",
        }
    return {
        "schema": "digivichi.trinity.dan-cycle.liveness-routing.v0",
        "source_status": "HEALTH_SUMMARY",
        "reason": "health_summary_read",
        "health_summary_path": str(path),
        "summary_age_seconds": age_seconds,
        "summary_max_age_seconds": max_age,
        "overall_status": summary.get("overall_status"),
        "agents": agents,
        "effect_scope": ["volume", "format", "timing"],
        "authority_boundary": {
            "alive_grants_authority": False,
            "executor_allowlist_only": True,
            "proposal_only_preserved": True,
            "gated_action_triggered_by_liveness": False,
            "capabilities_are_advisory_only": True,
        },
    }


def summarize_events(events: list[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for event in events:
        key = str(event.get("event", "unknown"))
        summary[key] = summary.get(key, 0) + 1
    return summary


def count_failed_checks(checks: list[dict[str, Any]]) -> int:
    return sum(1 for check in checks if check.get("status") not in ("SUCCEEDED", "SKIPPED"))


def check_result(name: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "status": result.get("status", "UNKNOWN"),
        "exit_code": result.get("exit_code"),
        "duration_seconds": result.get("duration_seconds"),
        "stdout_tail": tail(result.get("stdout", "")),
        "stderr_tail": tail(result.get("stderr", "")),
        "error": result.get("error"),
    }


def tail(value: Any, limit: int = 1200) -> str:
    text = trinity_executor.redact_sensitive(str(value or ""))
    if len(text) <= limit:
        return text
    return f"{text[-limit:]}\n...[tail {limit} of {len(text)} chars]"


def executor_context(root: Path, config: dict[str, Any], repo_root: Path) -> trinity_executor.ExecutorContext:
    stdout_limit, stderr_limit = trinity_executor.output_limits(config)
    return trinity_executor.ExecutorContext(
        repo_root=repo_root,
        bridge_root=root,
        config=config,
        max_stdout_chars=stdout_limit,
        max_stderr_chars=stderr_limit,
    )


def run_dan_checks(mode: str, root: Path, config: dict[str, Any], repo_root: Path, *, dry_run: bool = False) -> list[dict[str, Any]]:
    if mode not in CHECK_MODES:
        raise CycleError(f"unknown check mode: {mode}")
    if mode == "none":
        return []
    if dry_run:
        planned = ["axioms_floor"]
        if mode in ("trinity", "full"):
            planned.append("trinity_tests")
        if mode == "full":
            planned.append("full_ai_chi_tests")
        return [
            {
                "name": task_id,
                "status": "SKIPPED",
                "exit_code": None,
                "duration_seconds": 0,
                "stdout_tail": "dry run; check not executed",
                "stderr_tail": "",
                "error": None,
            }
            for task_id in planned
        ]

    context = executor_context(root, config, repo_root)
    checks = [check_result("axioms_floor", trinity_executor.TASKS["axioms_floor"].runner(context, {}))]
    if mode in ("trinity", "full"):
        checks.append(check_result("trinity_tests", trinity_executor.TASKS["trinity_tests"].runner(context, {})))
    if mode == "full":
        checks.append(check_result("full_ai_chi_tests", trinity_executor.TASKS["full_ai_chi_tests"].runner(context, {})))
    return checks


def make_cycle_summary_packet(cycle: dict[str, Any], targets: str | list[str]) -> dict[str, Any]:
    status = cycle["status"]
    target_list = trinity_bridge.normalize_targets(targets, "codex")
    liveness = cycle.get("liveness_routing") if isinstance(cycle.get("liveness_routing"), dict) else {}
    liveness_agents = liveness.get("agents") if isinstance(liveness.get("agents"), dict) else {}
    context_modes = {
        target: (liveness_agents.get(target, {}) if isinstance(liveness_agents.get(target), dict) else {}).get(
            "context_mode", "compact"
        )
        for target in target_list
    }
    packet_context_mode = "compact" if any(mode != "normal" for mode in context_modes.values()) else "normal"
    body = [
        f"cycle_id: {cycle['cycle_id']}",
        f"status: {status}",
        f"check_mode: {cycle['check_mode']}",
        f"summary_context_mode: {packet_context_mode}",
        f"liveness_source: {liveness.get('source_status', 'unknown')}",
        f"liveness_reason: {liveness.get('reason', 'unknown')}",
        f"liveness_targets: {context_modes}",
        f"arbitration_events: {cycle.get('arbitration_summary', {})}",
        f"route_events: {cycle['route_summary']}",
        f"executor_events: {cycle['executor_summary']}",
        f"failed_checks: {cycle['failed_checks']}",
        f"latest_state: {cycle.get('latest_state_path')}",
        f"ledger: {cycle.get('cycle_ledger_path')}",
    ]
    packet = {
        "schema": trinity_bridge.SCHEMA,
        "handoff_id": trinity_bridge.stable_id("cycle_summary"),
        "created_at": trinity_bridge.utc_now(),
        "from": "codex",
        "to": target_list,
        "kind": "cycle_summary",
        "priority": "LOW" if status == "SUCCEEDED" else "HIGH",
        "requires_user_approval": False,
        "mode": "stewardship",
        "objective": "Trinity+DAN cycle summary",
        "summary": f"{cycle['cycle_id']}: {status}, checks={cycle['check_mode']}, failed_checks={cycle['failed_checks']}",
        "body": "\n".join(body),
        "files_in_scope": [
            "scripts/trinity_dan_cycle.py",
            "scripts/trinity_arbitrator.py",
            "_MODEL_TRINITY/bridge/CYCLE_POLICY.md",
            "_MODEL_TRINITY/bridge/ARBITRATION_POLICY.md",
        ],
        "constraints": [
            "foreground local cycle",
            "repo-local bridge state only",
            "no model calls",
            "no MCP installs",
            "no global app config mutation",
        ],
        "forbidden_actions": [
            "start hidden background agents",
            "interpret free-form text as shell",
            "read credentials",
            "write service connectors",
            "mutate Claude or Antigravity global settings",
        ],
        "requested_output": "CycleReviewRecord",
        "liveness_routing": liveness,
    }
    if packet_context_mode == "normal":
        packet["cycle_result"] = cycle
    else:
        packet["cycle_result_digest"] = {
            "cycle_id": cycle["cycle_id"],
            "status": cycle["status"],
            "check_mode": cycle["check_mode"],
            "arbitration_summary": cycle.get("arbitration_summary", {}),
            "route_summary": cycle["route_summary"],
            "executor_summary": cycle["executor_summary"],
            "post_executor_route_summary": cycle.get("post_executor_route_summary", {}),
            "failed_checks": cycle["failed_checks"],
            "cycle_ledger_path": cycle.get("cycle_ledger_path"),
            "latest_state_path": cycle.get("latest_state_path"),
            "liveness_source": liveness.get("source_status"),
            "liveness_reason": liveness.get("reason"),
        }
    return packet


def run_cycle(
    root: Path,
    config: dict[str, Any],
    *,
    repo_root: Path | None = None,
    check_mode: str = "none",
    dry_run: bool = False,
    route_results: bool = True,
    post_summary: bool = False,
    summary_targets: str | list[str] = "claude,antigravity",
) -> dict[str, Any]:
    repo_root = (repo_root or repo_root_from_script()).resolve()
    started = time.monotonic()
    cycle_id = trinity_bridge.stable_id("cycle")
    started_at = trinity_bridge.utc_now()
    liveness = liveness_routing(root, config)

    arbitration_events = (
        trinity_arbitrator.arbitrate_once(root, config, dry_run=dry_run)
        if trinity_arbitrator.arbitration_enabled(config)
        else []
    )
    route_events = trinity_bridge.route_once(root, config, dry_run=dry_run)
    executor_events = trinity_executor.process_once(
        root,
        config,
        repo_root=repo_root,
        dry_run=dry_run,
        route_results=route_results and not dry_run,
    )
    post_executor_route_events: list[dict[str, Any]] = []
    if route_results and not dry_run:
        post_executor_route_events = trinity_bridge.route_once(root, config)
    checks = run_dan_checks(check_mode, root, config, repo_root, dry_run=dry_run)

    failed_checks = count_failed_checks(checks)
    status = "SUCCEEDED" if failed_checks == 0 else "FAILED"
    if dry_run:
        status = "DRY_RUN"

    bridge_status = trinity_bridge.status(root, config)
    executor_status = trinity_executor.status(root, config)
    completed_at = trinity_bridge.utc_now()
    duration_seconds = round(time.monotonic() - started, 3)

    cycle = {
        "schema": SCHEMA,
        "cycle_id": cycle_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": duration_seconds,
        "status": status,
        "dry_run": dry_run,
        "check_mode": check_mode,
        "arbitration_events": arbitration_events,
        "arbitration_summary": summarize_events(
            [{"event": event.get("classification", "unknown")} for event in arbitration_events]
        ),
        "route_events": route_events,
        "route_summary": summarize_events(route_events),
        "executor_events": executor_events,
        "executor_summary": summarize_events(executor_events),
        "post_executor_route_events": post_executor_route_events,
        "post_executor_route_summary": summarize_events(post_executor_route_events),
        "checks": checks,
        "failed_checks": failed_checks,
        "bridge_status": bridge_status,
        "executor_status": executor_status,
        "liveness_routing": liveness,
        "safety": {
            "hidden_background_service": False,
            "model_calls": False,
            "mcp_installs": False,
            "service_connector_writes": False,
            "global_app_config_mutation": False,
            "freeform_shell_execution": False,
            "liveness_can_auto_execute": False,
            "liveness_can_expand_authority": False,
            "liveness_gates_volume_not_authority": True,
        },
    }

    ledger = cycle_ledger_path(root, config)
    latest = latest_state_path(root, config)
    cycle["cycle_ledger_path"] = str(ledger)
    cycle["latest_state_path"] = str(latest)

    if not dry_run:
        trinity_bridge.append_jsonl(ledger, cycle)
        trinity_bridge.atomic_write_json(latest, cycle)

    summary_path = None
    summary_arbitration_events: list[dict[str, Any]] = []
    summary_route_events: list[dict[str, Any]] = []
    if post_summary:
        packet = make_cycle_summary_packet(cycle, summary_targets)
        if dry_run:
            summary_path = str(root / "outbox" / "codex" / f"{packet['handoff_id']}.json")
        else:
            summary_path = str(trinity_bridge.post_packet(root, packet))
            if route_results:
                summary_arbitration_events = (
                    trinity_arbitrator.arbitrate_once(root, config)
                    if trinity_arbitrator.arbitration_enabled(config)
                    else []
                )
                summary_route_events = trinity_bridge.route_once(root, config)
        cycle["summary_packet_path"] = summary_path
        cycle["summary_arbitration_events"] = summary_arbitration_events
        cycle["summary_arbitration_summary"] = summarize_events(
            [{"event": event.get("classification", "unknown")} for event in summary_arbitration_events]
        )
        cycle["summary_route_events"] = summary_route_events
        cycle["summary_route_summary"] = summarize_events(summary_route_events)
        if summary_route_events:
            cycle["summary_processed_path"] = summary_route_events[-1].get("processed_path")
            cycle["summary_deliveries"] = summary_route_events[-1].get("deliveries", [])
        if not dry_run:
            trinity_bridge.atomic_write_json(latest, cycle)

    return cycle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Foreground Trinity + DAN cycle runner.")
    parser.add_argument("--root", default=None, help="Bridge root. Defaults to _MODEL_TRINITY/bridge.")
    parser.add_argument("--config", default=None, help="Config path. Defaults to <root>/trinity-bridge.config.json.")
    parser.add_argument("--once", action="store_true", help="Run one cycle.")
    parser.add_argument("--watch", action="store_true", help="Run foreground cycles until interrupted.")
    parser.add_argument("--max-iterations", type=int, default=0, help="Limit watch iterations; 0 means forever.")
    parser.add_argument("--dry-run", action="store_true", help="Plan the cycle without moving/writing packets or running checks.")
    parser.add_argument("--check-mode", choices=CHECK_MODES, default="none", help="DAN checks to run.")
    parser.add_argument("--no-route-results", action="store_true", help="Do not route execution or summary result packets.")
    parser.add_argument("--post-summary", action="store_true", help="Post a compact cycle_summary packet from Codex.")
    parser.add_argument("--summary-targets", default="claude,antigravity", help="Comma-separated summary targets.")
    parser.add_argument("--status", action="store_true", help="Print bridge/executor/cycle status.")
    return parser


def status(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    latest = latest_state_path(root, config)
    latest_cycle: dict[str, Any] | None = None
    if latest.exists():
        try:
            latest_cycle = trinity_bridge.load_json(latest)
        except trinity_bridge.BridgeError:
            latest_cycle = {"error": "latest cycle state is invalid JSON"}
    return {
        "schema": "digivichi.trinity.dan-cycle-status.v0",
        "created_at": trinity_bridge.utc_now(),
        "bridge": trinity_bridge.status(root, config),
        "executor": trinity_executor.status(root, config),
        "arbitrator": trinity_arbitrator.status(root, config),
        "cycle_ledger_path": str(cycle_ledger_path(root, config)),
        "cycle_ledger_exists": cycle_ledger_path(root, config).exists(),
        "latest_state_path": str(latest),
        "latest_state_exists": latest.exists(),
        "latest_cycle": latest_cycle,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root, _config_path, config = load_environment(args)

    if args.status:
        print(json.dumps(status(root, config), indent=2, sort_keys=True))

    route_results = not args.no_route_results
    if args.once:
        cycle = run_cycle(
            root,
            config,
            check_mode=args.check_mode,
            dry_run=args.dry_run,
            route_results=route_results,
            post_summary=args.post_summary,
            summary_targets=args.summary_targets,
        )
        print(json.dumps(cycle, indent=2, sort_keys=True))

    if args.watch:
        interval = float(cycle_config(config).get("poll_interval_seconds", config.get("poll_interval_seconds", 2.0)))
        iteration = 0
        while True:
            iteration += 1
            cycle = run_cycle(
                root,
                config,
                check_mode=args.check_mode,
                dry_run=args.dry_run,
                route_results=route_results,
                post_summary=args.post_summary,
                summary_targets=args.summary_targets,
            )
            print(json.dumps({"event": "cycle", "iteration": iteration, "cycle": cycle}, sort_keys=True), flush=True)
            if args.max_iterations and iteration >= args.max_iterations:
                break
            time.sleep(interval)

    if not any((args.status, args.once, args.watch)):
        build_parser().print_help()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CycleError, trinity_bridge.BridgeError, trinity_executor.ExecutorError) as exc:
        print(json.dumps({"schema": "digivichi.trinity.dan-cycle-error.v0", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)

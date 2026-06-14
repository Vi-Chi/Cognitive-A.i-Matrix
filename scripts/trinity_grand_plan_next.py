"""Select repo-contained Grand Plan next tasks for Accelerated DAN.

The scanner is local-only. It reads bounded project/backlog surfaces, ranks
safe-looking repo tasks, labels gated work as blocked, and can emit a
non-action Trinity handoff packet for offline models.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "digivichi.trinity.grand-plan-next-tasks.v0"
PACKET_REQUESTED_OUTPUT = "GrandPlanNextTasks"
DEFAULT_LIMIT = 8
MAX_FILE_BYTES = 12000
MAX_FILES_PER_BUCKET = 120

SKIP_DIRS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "_backup",
    "_Import",
    "processed",
    "rejected",
    "ledger",
}

SAFE_TERMS = {
    "doc": 4,
    "docs": 4,
    "documentation": 5,
    "schema": 5,
    "schemas": 5,
    "test": 5,
    "tests": 5,
    "fixture": 4,
    "fixtures": 4,
    "report": 4,
    "handoff": 4,
    "backlog": 4,
    "risk": 3,
    "contradiction": 4,
    "dry-run": 5,
    "dry run": 5,
    "validation": 5,
    "validate": 4,
    "local": 3,
    "offline": 3,
    "plan": 3,
    "patch": 3,
}

GATED_PATTERNS = {
    "provider/API call": re.compile(r"\b(provider|api call|openai|anthropic|gemini|model call)\b", re.I),
    "secret or credential": re.compile(r"\b(secret|credential|api key|token|keys\.txt|fingerprint|rotation|adoption)\b", re.I),
    "MCP/plugin install": re.compile(r"\b(mcp install|plugin install|install plugins?|install mcp)\b", re.I),
    "app config mutation": re.compile(r"\b(app config|config\.toml|claude_desktop_config|settings mutation)\b", re.I),
    "network listener or broker": re.compile(r"\b(listener|broker|socket|nats|websocket|public bind|0\.0\.0\.0)\b", re.I),
    "public/service write": re.compile(r"\b(public post|deploy|deployment|github push|merge|release|service write|drive sharing)\b", re.I),
    "Docker/firewall/live stack": re.compile(r"\b(docker|firewall|vpn|service start|live stack)\b", re.I),
    "spending": re.compile(r"\b(spend|spending|procurement|paid|billing|treasury real)\b", re.I),
    "destructive operation": re.compile(r"\b(delete|destructive|remove old|wipe|reset --hard)\b", re.I),
    "physical actuation": re.compile(r"\b(actuator|vessel|rudder|engine|drone|submarine|rf transmit|autopilot)\b", re.I),
}

TASK_LINE_RE = re.compile(
    r"^\s*(?:(?:[-*]|\d+\.)\s*)?(?:\*\*)?(?P<marker>Next safe task|Next recommended step|Action item|TODO|FIXME|NEXT(?: STEP)?|Recommended|Remaining|Backlog|Blocked|Risk|RADAR|WIP|Open|Codex\s*\(open\)|Claude\s*\(open\)|Antigravity\s*\(open\)|Before liveness feeds|Before)(?:\*\*)?(?=\s*[:\-\]]|\s|$)[:\-\]]?\s*(?P<text>.*)",
    re.I,
)
DATE_RE = re.compile(r"(20\d{2})[-_](\d{2})[-_](\d{2})")
COMPLETION_RE = re.compile(
    r"\b(done|closed|completed|implemented|verified)\b|\bcomplete\s*(?:[-\u2013\u2014:.,]|$)|\bcomplete for\b|no action required|none required|\bpass:\b",
    re.I,
)
HANDOFF_MARKERS = ("recommended model", "handoff target", "next agent handoff", "next handoff")


@dataclass(frozen=True)
class Candidate:
    source_type: str
    source_path: str
    evidence: str
    title: str
    score: int
    gated_actions: tuple[str, ...]
    recommended_model: str
    superseded_source: bool = False
    completion_hint: bool = False
    current_state_source: bool = False
    stale_source: bool = False

    @property
    def is_safe(self) -> bool:
        return not self.gated_actions


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def is_skipped(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    return any(part in SKIP_DIRS for part in relative.parts)


def read_text_limited(path: Path) -> str:
    data = path.read_bytes()[:MAX_FILE_BYTES]
    return data.decode("utf-8", errors="replace")


def short_line(text: str, limit: int = 220) -> str:
    collapsed = " ".join(text.strip().split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3] + "..."


def find_gates(text: str) -> tuple[str, ...]:
    return tuple(label for label, pattern in GATED_PATTERNS.items() if pattern.search(text))


def score_text(text: str, source_type: str) -> int:
    lowered = text.lower()
    score = 0
    for term, weight in SAFE_TERMS.items():
        if term in lowered:
            score += weight
    if source_type in {"roadmap", "todo_next"}:
        score += 8
    if source_type == "bridge_inbox":
        score += 3
    if source_type in {"report", "knowledge_base"}:
        score += 4
    if "next safe" in lowered or "next recommended" in lowered:
        score += 18
    if "open" in lowered:
        score += 6
    if "test" in lowered and ("todo" in lowered or "missing" in lowered):
        score += 5
    return score


def completion_hint(text: str) -> bool:
    return bool(COMPLETION_RE.search(text))


def state_snapshot_date(path: Path) -> str:
    match = re.search(r"STATE_OF_SYSTEM_(\d{4}-\d{2}-\d{2})\.md$", path.name)
    return match.group(1) if match else ""


def source_date(path: Path) -> str:
    snapshot_date = state_snapshot_date(path)
    if snapshot_date:
        return snapshot_date
    match = DATE_RE.search(path.as_posix())
    if not match:
        return ""
    return "-".join(match.groups())


def latest_state_snapshot(root: Path) -> Path | None:
    kb = root / "_PROJECT_KNOWLEDGE_BASE"
    snapshots = sorted(
        (path for path in kb.glob("STATE_OF_SYSTEM_*.md") if path.is_file()),
        key=state_snapshot_date,
    )
    return snapshots[-1] if snapshots else None


def explicit_superseded_paths(root: Path) -> set[str]:
    superseded: set[str] = set()
    kb = root / "_PROJECT_KNOWLEDGE_BASE"
    if not kb.exists():
        return superseded
    for path in kb.rglob("*.md"):
        try:
            text = read_text_limited(path)
        except OSError:
            continue
        for name in re.findall(r"Supersedes\s+`([^`]+)`", text, flags=re.I):
            target = (path.parent / name).resolve()
            try:
                superseded.add(target.relative_to(root.resolve()).as_posix())
            except ValueError:
                superseded.add(name.replace("\\", "/"))
    latest = latest_state_snapshot(root)
    for path in kb.glob("STATE_OF_SYSTEM_*.md"):
        if path.is_file() and latest and path.resolve() != latest.resolve():
            superseded.add(path.relative_to(root).as_posix())
    return superseded


def recommended_model(text: str, source_type: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ("audit", "review", "risk", "contradiction", "verify wording")):
        return "claude"
    if any(term in lowered for term in ("scout", "proposal", "options", "research")):
        return "antigravity"
    if source_type == "bridge_inbox" and "claude" in lowered and "codex" not in lowered:
        return "claude"
    return "codex"


def source_type_for(path: Path, root: Path) -> str:
    name = path.name.lower()
    rel = path.relative_to(root).as_posix().lower()
    if "live_capability_approvals.md" in name:
        return "live_capability_approvals"
    if "roadmap" in name:
        return "roadmap"
    if "todo" in name or "next_step" in name or "next-step" in name:
        return "todo_next"
    if rel.startswith("_project_knowledge_base/reports/"):
        return "report"
    if rel.startswith("_project_knowledge_base/"):
        return "knowledge_base"
    if rel.startswith("_model_trinity/"):
        return "trinity_policy"
    if rel.startswith("docs/"):
        return "docs"
    if "/tests/" in rel or rel.startswith("ai_chi/tests/"):
        return "tests"
    return "repo_doc"


def contributes_task_candidates(path: Path, root: Path, source_type: str) -> bool:
    name = path.name.lower()
    rel = path.relative_to(root).as_posix().lower()
    if source_type in {"roadmap", "todo_next", "report", "knowledge_base", "tests", "live_capability_approvals"}:
        return True
    if source_type == "trinity_policy":
        return any(token in name for token in ("risk", "handoff", "report", "roadmap", "todo", "next"))
    if source_type == "docs":
        return any(token in name for token in ("roadmap", "todo", "next", "risk", "report"))
    if source_type == "repo_doc":
        return rel.endswith("live_capability_approvals.md")
    return False


def iter_candidate_files(root: Path) -> Iterable[Path]:
    front_door = [
        "DO_ANYTHING_NOW.md",
        "AGENTS.md",
        "CLAUDE.md",
        "ANTIGRAVITY.md",
        "README.md",
        "LIVE_CAPABILITY_APPROVALS.md",
        "_PROJECT_KNOWLEDGE_BASE/README.md",
        "_PROJECT_KNOWLEDGE_BASE/STATE_OF_SYSTEM_2026-06-14.md",
        "_PROJECT_KNOWLEDGE_BASE/STATE_OF_SYSTEM_2026-06-12.md",
        "_PROJECT_KNOWLEDGE_BASE/SMTIS_MARITIME_APP.md",
        "_PROJECT_KNOWLEDGE_BASE/RESEARCH_LIBRARY.md",
        "_MODEL_TRINITY/README.md",
        "_MODEL_TRINITY/TRINITY_RISK_REGISTER.md",
        "_MODEL_TRINITY/GRAND_PLAN_LOCAL_OPERATOR_MODE.md",
    ]
    yielded: set[Path] = set()
    for relative in front_door:
        path = root / relative
        if path.exists() and path.is_file():
            yielded.add(path)
            yield path

    roots = [
        root / "docs",
        root / "_MODEL_TRINITY",
        root / "_PROJECT_KNOWLEDGE_BASE",
        root / "ai_chi" / "tests",
    ]
    count = 0
    for base in roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if count >= MAX_FILES_PER_BUCKET * len(roots):
                return
            if not path.is_file() or is_skipped(path, root):
                continue
            name = path.name.lower()
            rel = path.relative_to(root).as_posix().lower()
            interesting_name = any(token in name for token in ("roadmap", "todo", "next_step", "next-step"))
            interesting_area = rel.startswith("_project_knowledge_base/reports/") or rel.startswith("_model_trinity/")
            if path.suffix.lower() in {".md", ".txt", ".py"} and (interesting_name or interesting_area):
                if path not in yielded:
                    yielded.add(path)
                    count += 1
                    yield path


def extract_candidates_from_file(
    path: Path,
    root: Path,
    *,
    superseded_paths: set[str] | None = None,
    current_state_path: str | None = None,
    current_state_date: str = "",
) -> list[Candidate]:
    source_type = source_type_for(path, root)
    if not contributes_task_candidates(path, root, source_type):
        return []
    try:
        text = read_text_limited(path)
    except OSError:
        return []
    candidates: list[Candidate] = []
    source_rel = path.relative_to(root).as_posix()
    source_is_superseded = source_rel in (superseded_paths or set())
    source_is_current_state = source_rel == current_state_path
    dated_source = source_date(path)
    source_is_stale = bool(
        source_type == "report"
        and current_state_date
        and dated_source
        and dated_source < current_state_date
    )
    for index, line in enumerate(text.splitlines(), start=1):
        if re.match(r"^\s*[-*]\s*\*\*Open\s+\((?:Codex|Claude|Antigravity)\)", line, re.I):
            continue
        match = TASK_LINE_RE.search(line)
        if not match:
            continue
        title = short_line(match.group("text") or line)
        title = title.strip("* ")
        if not title:
            title = short_line(line)
        title_lower = title.lower()
        if len(title) < 12 or title.startswith((",", ";", "and ", "or ")):
            continue
        if any(marker in title_lower for marker in HANDOFF_MARKERS):
            continue
        evidence = f"{path.relative_to(root).as_posix()}:{index}"
        context = f"{line}\n{title}"
        gates = find_gates(context)
        base_score = score_text(context, source_type)
        line_completion_hint = completion_hint(context)
        if source_is_current_state:
            base_score += 22
        if source_is_stale:
            base_score -= 12
        if source_is_superseded:
            base_score -= 30
        if line_completion_hint:
            base_score -= 20
        if gates:
            base_score -= 15
        candidates.append(
            Candidate(
                source_type=source_type,
                source_path=source_rel,
                evidence=evidence,
                title=title,
                score=base_score,
                gated_actions=gates,
                recommended_model=recommended_model(context, source_type),
                superseded_source=source_is_superseded,
                completion_hint=line_completion_hint,
                current_state_source=source_is_current_state,
                stale_source=source_is_stale,
            )
        )
    return candidates


def load_bridge_packet(path: Path) -> dict[str, Any] | None:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def extract_candidates_from_bridge_inbox(root: Path, role: str = "codex") -> list[Candidate]:
    inbox = root / "_MODEL_TRINITY" / "bridge" / "inbox" / role
    if not inbox.exists():
        return []
    packets = sorted(inbox.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)[:40]
    candidates: list[Candidate] = []
    for path in packets:
        packet = load_bridge_packet(path)
        if not packet:
            continue
        fields = [
            str(packet.get("objective") or ""),
            str(packet.get("summary") or ""),
            str(packet.get("requested_output") or ""),
            " ".join(str(item) for item in packet.get("files_in_scope", []) if item),
        ]
        text = short_line(" ".join(part for part in fields if part), 260)
        if not text:
            continue
        gates = find_gates(text)
        line_completion_hint = completion_hint(text)
        candidates.append(
            Candidate(
                source_type="bridge_inbox",
                source_path=path.relative_to(root).as_posix(),
                evidence=f"{path.relative_to(root).as_posix()}:metadata",
                title=text,
                score=score_text(text, "bridge_inbox") - (15 if gates else 0) - (20 if line_completion_hint else 0),
                gated_actions=gates,
                recommended_model=recommended_model(text, "bridge_inbox"),
                completion_hint=line_completion_hint,
            )
        )
    return candidates


def candidate_to_record(candidate: Candidate, rank: int) -> dict[str, Any]:
    allowed_actions = [
        "local docs/report/schema/test work",
        "repo-contained patch plan",
        "safe validation commands",
        "bridge handoff packet",
    ]
    if candidate.source_type == "live_capability_approvals":
        allowed_actions = ["draft approval packet only", "do not execute gated action"]
    return {
        "rank": rank,
        "title": candidate.title,
        "source_type": candidate.source_type,
        "source_path": candidate.source_path,
        "evidence": candidate.evidence,
        "score": candidate.score,
        "safe_for_local_execution": candidate.is_safe and candidate.source_type != "live_capability_approvals",
        "allowed_actions": allowed_actions,
        "gated_actions": list(candidate.gated_actions),
        "recommended_model": candidate.recommended_model,
        "superseded_source": candidate.superseded_source,
        "completion_hint": candidate.completion_hint,
        "current_state_source": candidate.current_state_source,
        "stale_source": candidate.stale_source,
    }


def build_report(root: Path, *, role: str = "codex", limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
    candidates: list[Candidate] = []
    files_checked: list[str] = []
    superseded_paths = explicit_superseded_paths(root)
    latest_state = latest_state_snapshot(root)
    latest_state_rel = latest_state.relative_to(root).as_posix() if latest_state else None
    latest_state_date = state_snapshot_date(latest_state) if latest_state else ""
    for path in iter_candidate_files(root):
        files_checked.append(path.relative_to(root).as_posix())
        candidates.extend(
            extract_candidates_from_file(
                path,
                root,
                superseded_paths=superseded_paths,
                current_state_path=latest_state_rel,
                current_state_date=latest_state_date,
            )
        )
    candidates.extend(extract_candidates_from_bridge_inbox(root, role=role))

    deduped: dict[tuple[str, str], Candidate] = {}
    for candidate in candidates:
        key = (candidate.source_path, candidate.title.lower())
        current = deduped.get(key)
        if current is None or candidate.score > current.score:
            deduped[key] = candidate

    sorted_candidates = sorted(
        deduped.values(),
        key=lambda item: (item.is_safe, item.score, item.source_type != "live_capability_approvals"),
        reverse=True,
    )
    selected = sorted_candidates[: max(1, limit)]

    if not selected:
        selected_records = [
            {
                "rank": 1,
                "title": "Run Grand Plan surface map and create ranked local next tasks.",
                "source_type": "fallback",
                "source_path": "_MODEL_TRINITY/GRAND_PLAN_LOCAL_OPERATOR_MODE.md",
                "evidence": "_MODEL_TRINITY/GRAND_PLAN_LOCAL_OPERATOR_MODE.md:Fallback Packet",
                "score": 0,
                "safe_for_local_execution": True,
                "allowed_actions": ["local docs/report/backlog packet", "safe validation commands"],
                "gated_actions": [],
                "recommended_model": "codex",
            }
        ]
    else:
        selected_records = [candidate_to_record(candidate, index + 1) for index, candidate in enumerate(selected)]

    return {
        "schema": SCHEMA,
        "created_at": utc_now(),
        "mode": "Accelerated DAN / Grand Plan Local Operator Mode",
        "repo_root": str(root),
        "role": role,
        "backlog_sources_checked": {
            "files": files_checked,
            "bridge_inbox_role": role,
            "live_capability_approvals_checked": any(path.endswith("LIVE_CAPABILITY_APPROVALS.md") for path in files_checked),
            "superseded_sources_detected": sorted(superseded_paths),
            "current_state_snapshot": latest_state_rel,
            "current_state_date": latest_state_date,
        },
        "selected_tasks": selected_records,
        "still_forbidden_without_exact_approval": [
            "provider/API calls",
            "secret reading, moving, printing, fingerprinting, rotation, or adoption",
            "MCP/plugin installs",
            "app config mutation",
            "network listeners or brokers",
            "public posting or deployment",
            "GitHub push, merge, release, or visibility changes",
            "Docker, firewall, service, or live-stack mutation",
            "spending",
            "destructive file operations",
        ],
        "recommended_next_handoff": next((task["recommended_model"] for task in selected_records if task["recommended_model"] != role), "claude"),
    }


def report_to_packet(report: dict[str, Any], targets: str) -> dict[str, Any]:
    tasks = report["selected_tasks"]
    body_lines = [
        f"mode: {report['mode']}",
        f"created_at: {report['created_at']}",
        "selected_tasks:",
    ]
    for task in tasks:
        body_lines.append(
            f"- rank {task['rank']}: {task['title']} | source={task['evidence']} | owner={task['recommended_model']} | safe={task['safe_for_local_execution']}"
        )
    body_lines.append("gates remain closed: provider/API calls, secrets, installs, app config, listeners, public writes, push/merge, Docker/firewall/live stack, spending, destructive ops")

    return {
        "schema": "digivichi.trinity.handoff.v0",
        "handoff_id": f"grand_plan_next_tasks_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "created_at": utc_now(),
        "from": "codex",
        "to": targets,
        "kind": "grand_plan_next_tasks",
        "priority": "MEDIUM",
        "requires_user_approval": False,
        "mode": "Accelerated DAN / Grand Plan Local Operator Mode",
        "objective": "Rank safe repo-contained Grand Plan next tasks for offline Trinity continuation.",
        "summary": f"GrandPlanNextTasks: {len(tasks)} ranked local actions; external gates remain closed.",
        "body": "\n".join(body_lines),
        "files_in_scope": [
            "_MODEL_TRINITY/GRAND_PLAN_LOCAL_OPERATOR_MODE.md",
            "scripts/trinity_grand_plan_next.py",
        ],
        "constraints": [
            "local repo-contained work only",
            "informational packet; does not request gated execution",
            "LIVE_CAPABILITY_APPROVALS may draft approvals only",
        ],
        "forbidden_actions": report["still_forbidden_without_exact_approval"],
        "evidence_refs": [task["evidence"] for task in tasks],
        "requested_output": PACKET_REQUESTED_OUTPUT,
        "grand_plan_next_tasks": report,
    }


def emit_packet(root: Path, packet: dict[str, Any], *, route_now: bool = False) -> dict[str, Any]:
    sys.path.insert(0, str(root / "scripts"))
    import trinity_bridge  # type: ignore

    bridge_root = trinity_bridge.resolve_root(None, base=root)
    config_path = bridge_root / "trinity-bridge.config.json"
    config = trinity_bridge.load_config(config_path if config_path.exists() else None, bridge_root=bridge_root)
    bridge_root = trinity_bridge.config_bridge_root(config, base=root)
    trinity_bridge.ensure_bridge(bridge_root, config_path if config_path.exists() else None)
    path = trinity_bridge.post_packet(bridge_root, packet)
    result: dict[str, Any] = {"event": "posted", "path": str(path), "handoff_id": packet["handoff_id"]}
    if route_now:
        result["route_events"] = trinity_bridge.route_once(bridge_root, config)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rank safe Grand Plan next tasks for Accelerated DAN.")
    parser.add_argument("--repo-root", default=None, help="Repository root. Defaults to parent of scripts/.")
    parser.add_argument("--role", default="codex", choices=("codex", "claude", "antigravity"))
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--emit-packet", action="store_true", help="Post a GrandPlanNextTasks handoff packet from Codex.")
    parser.add_argument("--targets", default="claude,antigravity", help="Comma-separated packet targets.")
    parser.add_argument("--route-now", action="store_true", help="Route the emitted packet immediately.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from_script().resolve()
    report = build_report(root, role=args.role, limit=args.limit)
    if args.emit_packet:
        packet = report_to_packet(report, args.targets)
        report["packet"] = emit_packet(root, packet, route_now=args.route_now)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

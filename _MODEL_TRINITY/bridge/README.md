# Trinity Bridge

Status: ACTIVE local bridge scaffold, 2026-06-13.

This folder is a local file-backed bridge for Codex, Claude, and
Antigravity/Gemini. It routes JSON handoff packets among agent inboxes and
outboxes. It does not execute instructions, call models, start services, install
plugins, configure MCP servers, or publish anything externally.

Safe deterministic execution requests are handled by the separate Codex-side
executor documented in `EXECUTOR_POLICY.md`. The bridge itself remains a relay.
The foreground Trinity+DAN cycle runner is documented in `CYCLE_POLICY.md`.
The pre-route work-queue arbitrator is documented in
`ARBITRATION_POLICY.md`; record shapes are documented in
`ARBITRATION_SCHEMA.md`.

## Folders

- `outbox/codex`, `outbox/claude`, `outbox/antigravity` - each agent writes new
  packets here.
- `inbox/codex`, `inbox/claude`, `inbox/antigravity` - routed packets for each
  target agent.
- `processed/<agent>` - originals after successful routing.
- `rejected/<agent>` - invalid or unsafe packets plus reason files.
- `ledger/route-ledger.jsonl` - append-only route/reject events.
- `ledger/execution-ledger.jsonl` - append-only executor events.
- `ledger/arbitration-ledger.jsonl` - append-only arbitration events.
- `ledger/cycle-ledger.jsonl` - append-only Trinity+DAN cycle events.
- `health/<agent>/heartbeat.json` - latest local liveness heartbeat.
- `health/<agent>/heartbeat_history.ndjson` - append-only heartbeat history.
- `health/downtime_events.ndjson` - DOWN_STARTED and RECOVERED transitions.
- `health/health_summary.json` - latest token-routing health summary.
- `health/poke_requests.ndjson` and `health/poke_responses.ndjson` - local
  liveness poke records.
- `quota/config/quota_guard.config.example.json` - safe manual quota config
  template.
- `quota/snapshots/<agent>.latest.json` and `quota/events/*.jsonl` - optional
  local evidence for quota/session state; no provider dashboards or secrets.
- `quota/downtime/YYYY-MM-DD.downtime.jsonl` - quota/session downtime records.
- `quota/state/quota_guard_status.json` - latest quota guard summary.
- `claims/` - packet claim locks for safe routed work.
- `state/compact-handoffs/` - compact handoff deltas for token-efficient review.
- `executed/codex` - structured execution requests completed by Codex.
- `execution_rejected/codex` - execution requests refused by policy.
- `needs_human/`, `blocked/`, `stale/`, `superseded/`,
  `arbitration_rejected/` - typed arbitration quarantine folders.
- `samples/` - example packets.
- `state/latest-arbitration.json` - latest arbitration pass status.
- `state/latest-cycle.json` - latest Trinity+DAN cycle status.

## Packet Shape

```json
{
  "schema": "digivichi.trinity.handoff.v0",
  "from": "codex",
  "to": ["claude", "antigravity"],
  "kind": "handoff",
  "priority": "MEDIUM",
  "requires_user_approval": false,
  "mode": "review",
  "objective": "One sentence",
  "summary": "Compact summary",
  "body": "Instructions, findings, or handoff content.",
  "files_in_scope": ["path"],
  "constraints": ["short constraint"],
  "forbidden_actions": ["exact forbidden action"],
  "evidence_refs": ["path or URL"]
}
```

Action-like kinds such as `action_request`, `permission_request`,
`tool_request`, and `service_write_request` must set
`requires_user_approval=true`, or the bridge rejects the packet.

## Commands

Initialize folders and config:

```powershell
python scripts/trinity_bridge.py --init
```

Post a Codex handoff to Claude and Antigravity:

```powershell
python scripts/trinity_bridge.py --post --from codex --to claude,antigravity --kind handoff --objective "Review Trinity bridge" --body "Please review the bridge docs and tests."
```

Route pending outbox packets once:

```powershell
python scripts/trinity_bridge.py --once
```

Watch and route automatically in the foreground:

```powershell
python scripts/trinity_bridge.py --watch
```

Show queue status:

```powershell
python scripts/trinity_bridge.py --status
```

## Heartbeat Liveness

Write a local Codex heartbeat:

```powershell
python -m trinity_bridge.health.cli heartbeat --agent codex --bridge-root _MODEL_TRINITY\bridge
```

Poke a peer through its bridge inbox without granting authority:

```powershell
python -m trinity_bridge.health.cli poke --from-agent codex --to-agent claude --bridge-root _MODEL_TRINITY\bridge
```

Refresh the health summary and downtime records:

```powershell
python -m trinity_bridge.health.cli summarize --bridge-root _MODEL_TRINITY\bridge
python -m trinity_bridge.health.cli report --bridge-root _MODEL_TRINITY\bridge
```

Heartbeat and poke records are local-only coordination records. They do not
execute commands, mutate peer config, read secrets, start listeners, call
providers, spend, deploy, or write to public services.

## Quota Guard

Run one local quota/session pass:

```powershell
python tools/trinity_quota_guard.py --bridge _MODEL_TRINITY\bridge --once
```

Print a compact routing table:

```powershell
python tools/trinity_quota_guard.py --bridge _MODEL_TRINITY\bridge --status
```

Run a foreground quota loop:

```powershell
python tools/trinity_quota_guard.py --bridge _MODEL_TRINITY\bridge --interval 60
```

The quota guard reads local bridge heartbeats, metadata-only packet fields, and
manual quota snapshots/events. It does not read API keys, scrape dashboards,
call providers, mutate app config, enable paid credits, or start hidden
services. Quota pokes are metadata-only inbox packets that request status
snapshots and grant no tool/config/spending authority.

## Safe Executor

List allowlisted local tasks:

```powershell
python scripts/trinity_executor.py --list-tasks
```

Process structured execution requests once:

```powershell
python scripts/trinity_executor.py --once
```

Run the executor in the foreground:

```powershell
python scripts/trinity_executor.py --watch
```

Execution packets must use `kind: execution_request` plus a structured
`execution.task_id`. See `samples/claude-to-codex-execution-request.json`.

## Arbitrator

Arbitrate pending outbox packets once before routing:

```powershell
python scripts/trinity_arbitrator.py --once
```

Preview arbitration without moving packets:

```powershell
python scripts/trinity_arbitrator.py --once --dry-run
```

Write the default capability manifest:

```powershell
python scripts/trinity_arbitrator.py --write-capabilities
```

## Trinity+DAN Cycle

Run one foreground maintenance cycle:

```powershell
python scripts/trinity_dan_cycle.py --once --check-mode quick
```

Show cycle status:

```powershell
python scripts/trinity_dan_cycle.py --status
```

Post a compact cycle summary to Claude and Antigravity:

```powershell
python scripts/trinity_dan_cycle.py --once --check-mode quick --post-summary
```

## Safety

- Foreground watch only; no hidden background agent is installed.
- File relay only; no command execution from packet contents.
- No network, service connector, or MCP writes.
- No free-form body-to-shell execution.
- The safe executor runs only hardcoded local task IDs.
- The arbitrator routes only `safe` packets; typed quarantine records are not
  automatic authority.
- The cycle runner is foreground and repo-local unless separately approved.
- Packets are records, not authority.
- Promotion still requires MΣBUS, Urbi, Orbi, and user gates where applicable.

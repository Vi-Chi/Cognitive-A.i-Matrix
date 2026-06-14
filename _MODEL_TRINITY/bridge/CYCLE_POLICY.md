# Trinity + DAN Cycle Policy

Status: ACTIVE local policy, 2026-06-13.

The Trinity + DAN cycle runner is a foreground, repo-local coordinator. It
combines the existing Trinity bridge and safe executor into one bounded
maintenance loop.

It is not a global app automation, not an MCP server, not an A2A bridge, not a
hidden background service, and not the Orbi Executor.

## Purpose

Reduce token load and manual coordination by turning the standard Trinity/DAN
maintenance loop into a repeatable local command:

```text
arbitrate outbox packets -> route safe handoffs -> process safe execution
requests -> run optional DAN checks -> write ledgers/state -> optionally post
compact cycle summaries
```

For explicit user `DAN`, `continue`, `enhance`, or equivalent continuation
requests, this command is the bridge/executor preflight. If no queued packets
exist, Codex should continue the grand plan through Accelerated DAN / Grand
Plan Local Operator Mode instead of ending after a health summary.

## Command

Run one normal cycle:

```powershell
python scripts/trinity_dan_cycle.py --once
```

Run a quick DAN floor check during the cycle:

```powershell
python scripts/trinity_dan_cycle.py --once --check-mode quick
```

Run Trinity-specific tests during the cycle:

```powershell
python scripts/trinity_dan_cycle.py --once --check-mode trinity
```

Run the full local suite during the cycle:

```powershell
python scripts/trinity_dan_cycle.py --once --check-mode full
```

Post a compact summary to Claude and Antigravity:

```powershell
python scripts/trinity_dan_cycle.py --once --check-mode quick --post-summary
```

Run in foreground watch mode:

```powershell
python scripts/trinity_dan_cycle.py --watch
```

## Check Modes

| Mode | Checks |
|---|---|
| `none` | Route bridge packets and process safe execution requests only. |
| `quick` | `none` + Axioms floor check. |
| `trinity` | `quick` + Trinity bridge/executor/cycle tests. |
| `full` | `trinity` + full `ai_chi` unittest discovery. |

## Records

Each non-dry-run cycle writes:

- `_MODEL_TRINITY/bridge/ledger/arbitration-ledger.jsonl`
- `_MODEL_TRINITY/bridge/ledger/cycle-ledger.jsonl`
- `_MODEL_TRINITY/bridge/state/latest-arbitration.json`
- `_MODEL_TRINITY/bridge/state/latest-cycle.json`

Each cycle may also read:

- `_MODEL_TRINITY/bridge/health/health_summary.json`

The runner only reads this liveness summary. It does not write heartbeats in the
hot path and does not become a self-attesting liveness source.

Safe packets may also receive:

- `_MODEL_TRINITY/bridge/claims/<handoff_id>.json`
- `_MODEL_TRINITY/bridge/state/compact-handoffs/<handoff_id>.json`

If `--post-summary` is used, Codex emits a `cycle_summary` packet through its
outbox and routes it to the requested targets when result routing is enabled.

## Liveness Gate

Liveness affects only cycle output volume, format, and timing. It never changes
which actions are authorized.

Hard rules:

- A peer being `ALIVE` must not cause execution, route-to-execute, escalation, or
  any task becoming reachable unless it was already authorized by the existing
  user-approval or executor-allowlist path.
- The executor allowlist remains the sole automatic execution authority.
- Heartbeat `capabilities` are advisory only.
- `health_summary.json` missing, stale, or unreadable means conservative
  fallback: treat peers as queue-only and compact-summary targets.
- Liveness may scale token/contact weight down, or back up to the existing
  normal ceiling; it may not raise authority above normal.
- Provider calls, NATS starts, credential work, public writes, spending,
  physical/RF actions, Docker/firewall/live-stack mutation, and service writes
  remain explicitly approval-gated regardless of liveness state.

The cycle ledger records a `liveness_routing` decision for after-the-fact audit.
For queue-only or degraded peers, `cycle_summary` packets use a compact
`cycle_result_digest` instead of embedding the full cycle result.

## Explicit User DAN Continuation

Use this rule only for an explicit user request in the active chat. Do not use
it for a passive heartbeat.

1. Run bridge-first checks and route any pending packets.
2. If real packets exist, prefer that queued work over new work.
3. If no packets exist and Claude/Antigravity are idle, sleeping, or quota
   limited, enter Accelerated DAN / Grand Plan Local Operator Mode.
4. Select the next safe task from current repository evidence: state files,
   reports, risk registers, ROADMAP/TODO/NEXT_STEP files, tests, bridge inbox
   records, active handoff docs, and `LIVE_CAPABILITY_APPROVALS.md` draft-only
   approval items.
5. Keep the scope local, reversible, and testable. Default to a medium or
   smaller stewardship budget unless the user requested a broader pass.
6. Record the evidence source, verification, and next handoff in the completion
   report.
7. If no safe implementation task is obvious, emit a `GrandPlanNextTasks` packet
   instead of stopping.

This is how Codex carries the work when the other Trinity participants are
offline. It preserves the same stop gates as every other Trinity/DAN cycle.

Helper:

```powershell
python scripts\trinity_grand_plan_next.py --limit 5
```

## Boundaries

- Foreground command only.
- No hidden background agents.
- No global Claude, Codex, or Antigravity config mutation.
- No MCP/plugin installs.
- No service connector writes.
- No model calls.
- No credential reads.
- No free-form body-to-shell execution.
- No physical, vessel, RF, Docker, network, deployment, or public-posting action.
- Approval-gated, stale, superseded, blocked, or invalid packets are quarantined
  by the arbitrator before bridge routing.

## Approval Gates

The cycle runner may run local deterministic checks within this workspace. It
must not be converted into a scheduled Codex automation, Claude hook, Antigravity
sidecar, Windows service, MCP server, or always-on listener without an explicit
task-specific approval and a rollback note.

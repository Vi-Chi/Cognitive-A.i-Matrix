# Cross-Model Handoffs

## Handoff Matrix

| From | To | Trigger | Expected output |
|---|---|---|---|
| Antigravity | Claude | UI prototype needs architecture or safety review | `ArchitectureReviewRecord` |
| Antigravity | Codex | Generated code needs hardening or tests | `PatchPlan` + `TestVerificationRecord` |
| Claude | Antigravity | UI or mockup exploration needed | `ComponentScaffoldRecord` |
| Claude | Codex | Exact implementation required | `PatchRecord` + `BuildReport` |
| Codex | Claude | Patch changes doctrine or architecture | `ReviewRecord` |
| Codex | Antigravity | Visual layout exploration needed | `UIMockupRecord` |
| Codex | Claude/Antigravity | Empty outbox after explicit DAN requires backlog continuation | `GrandPlanNextTasks` |

## Handoff Packet

Every cross-model handoff should include:

```yaml
objective: one sentence
from_model: codex|claude|antigravity|user
to_model: codex|claude|antigravity
mode: audit|patch|review|synthesize|scaffold
constraints:
  - short constraint
files_in_scope:
  - path
current_status: compact summary
known_failures:
  - compact failure or none
requested_output: exact artifact or record type
forbidden_actions:
  - exact forbidden action
approval_required: true|false
budget:
  max_tokens: optional integer
  max_runtime_seconds: optional integer
expires_at: optional ISO-8601 UTC timestamp
supersedes:
  - optional prior handoff_id
```

## GrandPlanNextTasks Packet

When explicit user DAN finds an empty bridge outbox and no implementation task is
obvious yet, Codex emits a non-action `GrandPlanNextTasks` packet instead of
stopping.

Required fields:

```yaml
kind: grand_plan_next_tasks
mode: Accelerated DAN / Grand Plan Local Operator Mode
requested_output: GrandPlanNextTasks
requires_user_approval: false
backlog_sources_checked:
  files:
    - path
  bridge_inbox_role: codex
selected_tasks:
  - rank: 1
    title: short task
    evidence: path:line or packet:metadata
    safe_for_local_execution: true|false
    allowed_actions:
      - local docs/report/schema/test work
    gated_actions:
      - exact gated action or none
    recommended_model: codex|claude|antigravity
still_forbidden_without_exact_approval:
  - provider/API calls
  - secrets
  - MCP/plugin installs
  - app config mutation
  - listeners/brokers/services
```

This packet may recommend work, but it does not grant execution authority for
gated actions.

Before bridge routing, `scripts/trinity_arbitrator.py` validates the packet
against `_MODEL_TRINITY/bridge/agent-capabilities.json`, writes claim locks for
safe packets, compacts parseable records, and quarantines packets classified as
`needs-human`, `blocked`, `stale`, `superseded`, or `invalid`.

## Cross-Configuration Rule

A model may directly edit another model's workbench profile only if the edit
includes:

1. target model;
2. reason;
3. expected improvement;
4. risk;
5. rollback note;
6. affected files;
7. whether user, MΣBUS, or Urbi approval is required.

Every such edit must be logged in `CONFIG_CHANGE_LOG.md`.

## Local Bridge

The local automatic bridge lives at `_MODEL_TRINITY/bridge/` and is operated by
`scripts/trinity_bridge.py`.

Agents write outbound JSON packets to:

- `_MODEL_TRINITY/bridge/outbox/codex/`
- `_MODEL_TRINITY/bridge/outbox/claude/`
- `_MODEL_TRINITY/bridge/outbox/antigravity/`

The bridge routes packets to:

- `_MODEL_TRINITY/bridge/inbox/codex/`
- `_MODEL_TRINITY/bridge/inbox/claude/`
- `_MODEL_TRINITY/bridge/inbox/antigravity/`

The bridge is a file relay only. It never executes packet contents, calls MCP
tools, invokes models, writes service connectors, installs plugins, or starts
hidden background agents.

## Safe Execution Requests

The bridge remains a file relay. Safe automatic execution is handled separately
by `scripts/trinity_executor.py`, which reads only Codex inbox packets with
`kind: execution_request`.

Execution requests must use a structured allowlist task:

```json
{
  "schema": "digivichi.trinity.handoff.v0",
  "from": "claude",
  "to": ["codex"],
  "kind": "execution_request",
  "objective": "Run a compact verification task.",
  "requires_user_approval": false,
  "execution": {
    "schema": "digivichi.trinity.execution-request.v0",
    "task_id": "bridge_status",
    "args": {},
    "reason": "Need compact status evidence."
  }
}
```

Codex returns `kind: execution_result` packets through its outbox. The executor
does not parse `body` as commands. Unknown task IDs, approval-required packets,
and malformed execution objects are rejected into `execution_rejected/codex/`
and logged in `ledger/execution-ledger.jsonl`.

## Trinity + DAN Cycle Runner

`scripts/trinity_dan_cycle.py` coordinates the arbitrator, local bridge, and
executor in a foreground loop. It may also run DAN checks by mode:

- `none` - route packets and process safe execution requests.
- `quick` - `none` plus Axioms floor.
- `trinity` - `quick` plus Trinity unit tests.
- `full` - `trinity` plus full `ai_chi` unittest discovery.

The runner writes `ledger/cycle-ledger.jsonl` and
`state/latest-cycle.json`. With `--post-summary`, Codex emits a compact
`cycle_summary` packet for Claude and/or Antigravity review.

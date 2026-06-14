# Trinity Safe Executor Policy

Status: ACTIVE local policy, 2026-06-13.

The Trinity executor is a narrow Codex-side clerk for safe, deterministic local
checks requested through the bridge. It is not the Orbi Executor and it is not a
general shell runner.

## Purpose

Reduce repeated token-heavy handoffs by letting Claude, Antigravity, or Codex ask
for compact verification receipts such as bridge status, Axioms floor checks, or
Trinity unit tests.

## Input Folder

The executor reads only:

```text
_MODEL_TRINITY/bridge/inbox/codex/*.json
```

It processes only packets with:

```json
{
  "kind": "execution_request",
  "to": ["codex"],
  "execution": {
    "schema": "digivichi.trinity.execution-request.v0",
    "task_id": "bridge_status",
    "args": {}
  }
}
```

All other handoff packets stay in the Codex inbox for normal model review.

## Allowed Task IDs

The allowlist is compiled into `scripts/trinity_executor.py`.

| Task ID | Effect |
|---|---|
| `bridge_status` | Report bridge queue counts. |
| `bridge_route_once_dry_run` | Validate pending routes without moving packets. |
| `doc_inventory` | Return compact root/Trinity/KB document inventory. |
| `axioms_floor` | Run `verify_floor()`. |
| `trinity_bridge_tests` | Run bridge unit tests. |
| `trinity_executor_tests` | Run executor unit tests. |
| `trinity_arbitrator_tests` | Run arbitrator unit tests. |
| `trinity_cycle_tests` | Run Trinity+DAN cycle unit tests. |
| `trinity_tests` | Run bridge + executor + arbitrator + cycle unit tests. |
| `full_ai_chi_tests` | Run full `ai_chi` unittest discovery. |

## Refusal Rules

The executor rejects and records the packet when:

- the packet is not valid JSON;
- `kind` is `execution_request` but `execution` is missing;
- `execution.task_id` is missing or unknown;
- the packet is not addressed to Codex;
- `requires_user_approval` or `approval_required` is true;
- `execution.args` is not a JSON object;
- the task is later marked approval-required.

Free-form `body` text is never executed.

## Output

Successful and rejected requests write:

- moved request: `executed/codex/` or `execution_rejected/codex/`;
- ledger event: `ledger/execution-ledger.jsonl`;
- result packet: `outbox/codex/*.json` with `kind: execution_result`.

Result packets can then be routed by `scripts/trinity_bridge.py --once` or by a
foreground bridge watch.

## Boundaries

- No `shell=True`.
- No model calls.
- No MCP installs.
- No service connector writes.
- No credential reads.
- No network mutation.
- No Docker control.
- No hidden background service.
- No writes outside repository-local bridge/report paths.

## Commands

List safe tasks:

```powershell
python scripts/trinity_executor.py --list-tasks
```

Process pending execution requests once:

```powershell
python scripts/trinity_executor.py --once
```

Run in the foreground:

```powershell
python scripts/trinity_executor.py --watch
```

Route result packets immediately after processing:

```powershell
python scripts/trinity_executor.py --once --route-results
```

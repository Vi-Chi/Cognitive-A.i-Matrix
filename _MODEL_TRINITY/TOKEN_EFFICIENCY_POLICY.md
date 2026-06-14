# DigiViCHI Trinity Token Efficiency Policy

Status: promoted config-layer policy, 2026-06-13.
Scope: Claude, Codex, Antigravity/Gemini, future local providers, and tool
adapters.

## Core Rule

Do not send the whole project, full logs, full tool schemas, or full files unless
required.

Use this order:

1. Compact state summary.
2. Targeted file map.
3. Relevant snippets or diffs only.
4. Full file only when patching requires it.
5. Full repo only for deliberate reconstruction passes.

## Context Packet Pattern

Each model should receive a compact packet:

```yaml
objective: one sentence
mode: audit|patch|review|synthesize
constraints:
  - 5 to 10 bullets max
files_in_scope:
  - explicit path
current_status: compact health summary
known_failures:
  - compact failure or none
requested_output: exact artifact type
forbidden_actions:
  - exact forbidden action
```

## MCP/Tool Minimization

- Use progressive discovery: load summaries before full schemas.
- Lazy-load full schemas only for tools required by the task.
- Prefer one scripted inspection pass over many tool roundtrips.
- Keep tool namespaces small and role-specific.
- Hide or ignore tools irrelevant to the current task.
- Use compact tool outputs by default; expand only on failure.

## Long-Running Agent Rule

When an agent uses tools repeatedly:

- retain only critical recent observations in chat;
- summarize older calls into a ledger note;
- store detailed artifacts on disk;
- pass paths, hashes, or line references instead of full content;
- preserve contradictions as records, not long chat history.

## Safe Execution Receipts

When a model needs routine local evidence, prefer a compact Trinity
`execution_request` over pasting long instructions or logs. Use only allowlisted
task IDs from `_MODEL_TRINITY/bridge/EXECUTOR_POLICY.md`.

Good requests:

- `bridge_status`
- `doc_inventory`
- `axioms_floor`
- `trinity_tests`

The result packet should carry the compact receipt, exit code, and ledger path.
Do not send full logs unless a failure requires deeper diagnosis.

## Cycle Summaries

For routine coordination, prefer `cycle_summary` packets produced by
`scripts/trinity_dan_cycle.py --post-summary` over full chat recaps. The packet
should include only:

- cycle ID;
- check mode;
- event counts;
- failed check count;
- ledger/state paths;
- compact stdout/stderr tails for failed checks.

## Arbitration Compaction

The pre-route arbitrator writes compact handoff deltas under:

```text
_MODEL_TRINITY/bridge/state/compact-handoffs/
```

Agents should read the compact delta first when a packet is old, repeated,
superseding a prior packet, or part of routine review. Open the full packet only
when implementing or auditing exact details.

## Forbidden Token Waste

- full dependency trees in every prompt;
- full README pasted repeatedly;
- full logs when the last relevant lines are enough;
- full MCP schemas for unused tools;
- unrelated global plugin lists;
- repeated project philosophy unless task-relevant.

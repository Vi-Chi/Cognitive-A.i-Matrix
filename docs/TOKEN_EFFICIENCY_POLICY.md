# DigiViCHI Trinity Token Efficiency Policy

Status: Top-priority draft 2026-06-13
Scope: Claude, Codex, Antigravity/Gemini, future local providers, MCP/tool adapters.

## Core rule

Do not send the whole project, full logs, full tool schemas, or full files unless required.

Use this order:

1. Compact state summary
2. Targeted file map
3. Relevant snippets/diffs only
4. Full file only when patching requires it
5. Full repo only for deliberate reconstruction passes

## Context packet pattern

Each model should receive a compact packet:

```yaml
objective: one sentence
mode: audit | patch | review | synthesize
constraints: 5-10 bullets max
files_in_scope: explicit paths
current_status: compact health summary
known_failures: compact list
requested_output: exact artifact type
forbidden_actions: exact list
```

## MCP/tool minimization

- Use progressive discovery: load a summary of tool groups first.
- Lazy-load full schemas only for the top-k tools required by the task.
- Prefer one scripted tool pass over many chat/tool roundtrips.
- Keep tool namespaces small and role-specific.
- Hide tools that are irrelevant to the current task.
- Use compact tool outputs by default; full outputs only on failure.

## Long-running agent rule

When an agent uses tools repeatedly:

- retain only last N critical observations
- summarize old tool calls into a ledger note
- store detailed artifacts on disk
- pass links/paths/hashes instead of full content
- preserve contradictions as records, not long chat history

## Service-health summaries

The watchdog emits compact summaries like:

```text
services=4 online=2 degraded=0 offline=2 critical_offline=1 proposals=3
```

Agents should consume this first, then request failed-service detail only when needed.

## Forbidden token waste

- full dependency trees in every prompt
- full README pasted repeatedly
- full logs when only last 50 lines matter
- full MCP schemas for unused tools
- unrelated global plugin lists
- repeated project philosophy unless task-relevant

# Trinity Arbitration Schemas

Status: ACTIVE schema documentation, 2026-06-13.

These are documentation schemas for the local file-backed arbitration layer.
The deterministic implementation lives in `scripts/trinity_arbitrator.py`.

## ArbitrationRecord

Written to `ledger/arbitration-ledger.jsonl` and included in
`state/latest-arbitration.json`.

```yaml
schema: digivichi.trinity.arbitration.v0
event: arbitrated|would_arbitrate
source: codex|claude|antigravity
path: original packet path
created_at: ISO-8601 UTC
handoff_id: stable packet id
classification: safe|needs-human|blocked|stale|superseded|invalid
reason: concise reason
targets:
  - codex|claude|antigravity
kind: packet kind
warnings:
  - optional warning
claim_path: optional path for safe packets
compact_path: optional compact state-delta path
quarantine_path: optional typed quarantine path
```

## CapabilityManifest

Stored at `_MODEL_TRINITY/bridge/agent-capabilities.json`.

```yaml
schema: digivichi.trinity.capabilities.v0
updated_at: ISO-8601 UTC
policy:
  packets_are_records_not_authority: true
  execution_requires_allowlisted_task: true
  approval_required_packets_are_quarantined: true
  freeform_shell_execution: false
  model_calls: false
  mcp_installs: false
  service_connector_writes: false
agents:
  codex|claude|antigravity:
    role: Engineer-Operator|Auditor-Scribe|Builder-Scout
    can_emit_kinds:
      - handoff
    can_receive_kinds:
      - handoff
    auto_executable_tasks:
      - bridge_status
```

## ClaimLock

Stored at `_MODEL_TRINITY/bridge/claims/<handoff_id>.json`.

```yaml
schema: digivichi.trinity.claim-lock.v0
handoff_id: packet id
claimed_by: trinity_arbitrator
claimed_at: ISO-8601 UTC
source: codex|claude|antigravity
targets:
  - codex|claude|antigravity
kind: packet kind
source_path: original outbox packet
status: CLAIMED_FOR_SAFE_ROUTING
```

## CompactHandoff

Stored at `_MODEL_TRINITY/bridge/state/compact-handoffs/<handoff_id>.json`.

```yaml
schema: digivichi.trinity.compact-handoff.v0
created_at: ISO-8601 UTC
handoff_id: packet id
classification: safe|needs-human|blocked|stale|superseded|invalid
reason: concise reason
from: codex|claude|antigravity
to:
  - codex|claude|antigravity
kind: packet kind
priority: LOW|MEDIUM|HIGH|CRITICAL
objective: compact objective
summary: compact summary
body_delta: redacted compact body text
files_in_scope:
  - path
requested_output: expected record type
approval_required: true|false
budget:
  max_tokens: optional integer
  max_runtime_seconds: optional integer
  max_iterations: optional integer
expires_at: optional ISO-8601 UTC
supersedes:
  - optional prior handoff id
```

## Quarantine Folders

```text
needs_human/<agent>/
blocked/<agent>/
stale/<agent>/
superseded/<agent>/
arbitration_rejected/<agent>/
```

Each moved packet receives a sibling `.reason.txt` file. Moving a packet into a
quarantine folder does not delete it and does not approve or execute it.


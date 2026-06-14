# Trinity Arbitration Policy

Status: ACTIVE local policy, 2026-06-13.

The Trinity arbitrator is the pre-route work-queue layer for the local bridge.
It decides whether a packet is safe to route, needs human review, is blocked,
is stale, is superseded, or is invalid.

It is not an Orbi Executor, not a model caller, not an MCP server, not a Claude
or Antigravity app controller, and not a hidden background service.

## Purpose

The bridge is a relay and the executor is an allowlisted clerk. The arbitrator
adds the missing queue discipline between them:

```text
outbox packet -> schema/capability check -> claim lock -> compact state delta
-> safe route or typed quarantine
```

This reduces token load because agents can read compact handoff records from
`state/compact-handoffs/` instead of reopening full packets or long chat logs.

## Classifications

| Classification | Meaning | Default action |
|---|---|---|
| `safe` | Passive handoff/result/summary, or allowlisted execution request. | Keep in outbox, add arbitration block, write claim and compact delta. |
| `needs-human` | Packet asks for approval or contains action-like intent. | Move to `needs_human/<agent>/`. |
| `blocked` | Capability manifest or claim lock prevents routing. | Move to `blocked/<agent>/`. |
| `stale` | `expires_at` is in the past. | Move to `stale/<agent>/`. |
| `superseded` | Another pending packet lists this packet in `supersedes`. | Move to `superseded/<agent>/`. |
| `invalid` | Malformed JSON, unsupported schema, bad budget/expiry, or unsafe execution task. | Move to `arbitration_rejected/<agent>/`. |

## Capability Manifest

The default manifest lives at:

```text
_MODEL_TRINITY/bridge/agent-capabilities.json
```

It records each model role, allowed emitted packet kinds, allowed received
packet kinds, and Codex's allowlisted automatic execution tasks. It is
documentation plus deterministic policy input for `scripts/trinity_arbitrator.py`.

## Claim Locks

Safe packets receive a claim lock:

```text
_MODEL_TRINITY/bridge/claims/<handoff_id>.json
```

The lock prevents duplicate processing by a second local worker. Existing
non-arbitrator locks block routing until they expire or are manually resolved.

## Compact Handoffs

Every parseable arbitration record writes a compact delta:

```text
_MODEL_TRINITY/bridge/state/compact-handoffs/<handoff_id>.json
```

The compact record preserves objective, summary, body tail, files in scope,
classification, budget, expiry, and requested output. It must not include
secrets; executor redaction is applied before writing compact text.

## Commands

Initialize folders and the default capability manifest:

```powershell
python scripts/trinity_arbitrator.py --init
```

Arbitrate pending outbox packets once:

```powershell
python scripts/trinity_arbitrator.py --once
```

Preview arbitration without moving files:

```powershell
python scripts/trinity_arbitrator.py --once --dry-run
```

Run in foreground watch mode:

```powershell
python scripts/trinity_arbitrator.py --watch
```

Show status:

```powershell
python scripts/trinity_arbitrator.py --status
```

## Boundaries

- No command execution.
- No free-form body-to-shell conversion.
- No model calls.
- No MCP/plugin installs.
- No service connector writes.
- No credential reads.
- No global Claude, Codex, or Antigravity config mutation.
- No hidden background service.

## Cycle Integration

`scripts/trinity_dan_cycle.py` runs arbitration before bridge routing when the
config has `arbitrator.enabled=true`. Only `safe` packets remain in the outbox
for routing during the cycle.


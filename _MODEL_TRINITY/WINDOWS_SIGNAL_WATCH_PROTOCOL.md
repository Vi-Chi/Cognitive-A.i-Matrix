# Windows Signal Watch Protocol

Status: ACTIVE local workflow automation policy, created 2026-06-14.

This protocol lets Codex and Claude use Windows notification/event hints to
accelerate Trinity DAN handoffs while preserving privacy and stop gates.

## Purpose

Use low-risk Windows and Claude-local signals to notice when a Trinity agent may
need attention:

- DAN handoff is ready;
- Claude session limit/quota/sleep/idle state appears;
- bridge outbox packets are pending;
- Claude/Codex handoff loop can continue safely.

The watch layer is a signal detector, not an executor and not a permission
grant.

## Current Codex Watch

Codex app heartbeat:

- ID: `trinity-claude-signal-watch`
- cadence: every 5 minutes;
- scope: current Codex thread;
- task: run bounded bridge/signal checks and continue the safe local DAN loop
  only when a real signal or bridge packet exists.
- passive heartbeat rule: if no bridge packet or new actionable signal exists,
  keep the update quiet and do not mutate repo files.
- explicit user DAN rule: if the user directly invokes `DAN`, `continue`,
  `enhance`, or equivalent continuation language, this protocol becomes a
  preflight. After bridge-first checks, Codex should enter Accelerated DAN /
  Grand Plan Local Operator Mode when no other model has queued work.

Local probe:

```powershell
$env:PYTHONPATH=(Get-Location).Path; python scripts\trinity_windows_signal_probe.py --since-minutes 15 --claude-log-lines 300
```

The probe returns compact JSON with:

- Trinity bridge counts;
- scoped Claude log keyword counts;
- Windows Push Notification Platform event metadata counts;
- explicit privacy booleans.

## Claude Watch Guidance

Claude may use its own safe local mechanisms to observe the same signals inside
its own workspace/sandbox, but should follow the same boundary:

- prefer `scripts/trinity_bridge.py --status` and routed bridge packets;
- prefer scoped Claude log/status checks over raw notification body scraping;
- treat Windows notification event logs as metadata hints only;
- emit review/handoff packets rather than self-approving action;
- ask Codex for deterministic local checks through bridge packets when needed.

Claude should not mutate Claude app config, install plugins, start services,
read secrets, or scrape notification bodies as part of watch setup.

## Allowed Signal Sources

Allowed by default:

- `_MODEL_TRINITY/bridge/outbox/*` and bridge status JSON;
- `_MODEL_TRINITY/bridge/inbox/*` structured packets routed to the current role;
- `scripts/trinity_windows_signal_probe.py` output;
- recent Claude `main.log` lines scanned for narrowly scoped keywords;
- `C:\Users\Vi Chi\.claude\status\claude-bridge-status.json` if present;
- Windows Push Notification Platform event metadata:
  - event count;
  - event id;
  - provider/log name;
  - timestamp.

## Forbidden Signal Sources Without Exact Approval

Do not read, scrape, export, or persist:

- raw Windows notification bodies;
- Windows notification databases;
- passwords, tokens, OAuth files, API keys, `keys.txt`, or private key material;
- Claude/Codex/Antigravity app config bodies for watch setup;
- browser/session stores;
- service connector payloads;
- email, calendar, Drive, chat, or social content;
- screenshots of private notifications.

## Escalation Rules

When a signal appears:

1. Check `scripts/trinity_bridge.py --status`.
2. If any outbox has pending packets, run `scripts/trinity_bridge.py --once`.
3. Inspect only structured/redacted packet fields for packets routed to the
   current role.
4. Execute only local allowlisted checks or safe repo patches requested by real
   packets.
5. Keep stop-gated work as proposals until exact owner approval is supplied.

If there is no bridge packet and only a generic notification/log hint during a
passive heartbeat, emit a brief status note or wait for the next heartbeat. Do
not invent work.

If the user explicitly invoked DAN or continuation in the current chat, do not
stop at the passive heartbeat rule. Continue with the documented Grand Plan
local operator loop:

```text
check backlog sources -> select safe repo-contained task -> implement the
smallest reversible improvement or create GrandPlanNextTasks -> verify -> record
-> hand off
```

This is not "invented work" when the task is selected from current repository
docs, bridge packets, reports, TODOs, tests, or risk records and the evidence
source is recorded in the completion report.

The durable mode policy is `_MODEL_TRINITY/GRAND_PLAN_LOCAL_OPERATOR_MODE.md`.

## Stop Gates Still Active

The watch layer does not authorize:

- provider calls or spending;
- credential reads, fingerprints, rotation, or adoption;
- app config mutation;
- MCP/plugin installs;
- Windows scheduled task or service installation;
- raw notification scraping;
- NATS, Signal-K, AIS, or other sockets/listeners;
- service writes, public deployment, or publication;
- physical/vessel/drone/submarine actuation.

## Verification

Useful checks:

```powershell
$env:PYTHONPATH=(Get-Location).Path; python scripts\trinity_windows_signal_probe.py --since-minutes 15 --claude-log-lines 300
python scripts\trinity_bridge.py --status
$env:PYTHONPATH=(Get-Location).Path; python scripts\check_trinity_secret_refs.py
```

Expected privacy invariants in probe output:

```text
raw_notification_text_read=false
credential_files_read=false
app_config_mutated=false
service_started=false
```

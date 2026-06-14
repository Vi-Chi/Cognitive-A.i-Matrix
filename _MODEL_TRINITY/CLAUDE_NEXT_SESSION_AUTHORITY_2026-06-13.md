# Claude Next Session Authority Grant

Status: ACTIVE for the next Claude session cycle only. Created 2026-06-13.

Owner signature supplied in chat: `Vichi`

## Scope

Claude is granted full authority inside its own Claude workspace/sandbox and the
repo-local Auditor-Scribe lane for the next session cycle. This is a bounded
Trinity/DAN grant, not unrestricted system control.

Claude may:

- read project docs, reports, profiles, schemas, bridge packets, and local
  verification outputs in this workspace;
- audit Codex and Antigravity work against `DO_ANYTHING_NOW.md`, the Axioms,
  Triad separation, MΣBUS/Urbi/Orbi gates, and user instructions;
- write review records, safety critiques, contradiction records, synthesis
  reports, and patch plans;
- emit Trinity bridge packets from `outbox/claude/` when they are records, not
  execution grants;
- make low-risk reversible documentation/profile edits that are listed in
  `_MODEL_TRINITY/CLAUDE_PROFILE.md` and do not cross a stop gate;
- request Codex implementation when tests, scripts, code patches, or local
  deterministic execution are needed.

## Stop Gates Still Active

This grant does not authorize:

- reading or exposing credentials unless the exact secret boundary is approved;
- spending money;
- service connector writes;
- app config mutation outside the explicitly named file/task;
- MCP or plugin installs;
- ICP/mainnet/on-chain writes;
- public deployment, publication, visibility changes, or SNS/token launch;
- destructive deletion;
- physical/vessel/drone/submarine actuation.

## Expected Next Session Cycle

1. Read `CLAUDE.md`, this file, `_MODEL_TRINITY/CLAUDE_PROFILE.md`, and the
   newest bridge inbox packets.
2. Confirm whether any pending packet is actionable.
3. If action is docs/profile-only and reversible, proceed in Auditor-Scribe lane.
4. If implementation, runtime, install, credential, service, spending, or public
   action is required, emit a Codex handoff or approval request instead of
   self-authorizing.
5. End with a DAN Completion Report and a compact bridge packet if Codex or
   Antigravity should continue.

## Expiry

Expires after one completed Claude session cycle or at 2026-06-14 23:59 local
time, whichever comes first. After expiry, treat this file as archival evidence
of a past scoped grant, not active authority.

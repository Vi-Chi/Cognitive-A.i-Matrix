# Accelerated DAN / Grand Plan Local Operator Mode

Status: ACTIVE local workflow policy, created 2026-06-14.

This mode replaces the obsolete "empty bridge outbox means idle" behavior for
explicit user DAN or continuation requests.

## Rule

When the user directly invokes `DAN`, `continue`, `enhance`, `build`, or
equivalent continuation language, Codex must not stop after a clean bridge
status or safe quick cycle.

If the Trinity bridge outbox is empty, Codex should select the next safe
repo-contained task from the Grand Plan backlog and continue project progress.

## Interpretation

Bounded DAN remains valid at external and live authority gates. It must not mean
bounded into inactivity.

In this repository:

- bounded at gates means no provider calls, spending, secrets, services,
  public writes, app config mutation, MCP/plugin installs, Docker/network/live
  stack changes, or destructive operations without exact approval;
- accelerated locally means Codex may infer and execute safe repo-contained
  documentation, schema, test, report, handoff, backlog, dry-run, and validation
  work from current project evidence.

## Synthesis Engine vs Diagnostics (The Design Pivot)

The Grand Plan is no longer just a diagnostic task runner. It operates the **Historical-Metaphorical Synthesis Engine**.

When the system encounters history, science fiction, mythic patterns, game systems, hardware limits, memory models, economics, or agent workflows (typically within `_Import` or raw chat logs), Codex must synthesize them into explicit **Conjectures**.

Conjectures map external domains to actionable project architecture.

### The Canon Boundary (CRITICAL)

A Conjecture is **never** direct Canon.
- Synthesized insights must be explicitly labeled: `Status: Conjecture`.
- Conjectures live in `_PROJECT_KNOWLEDGE_BASE/conjectures/` or as explicitly non-canon reports.
- Conjectures may only become active codebase/Canon after they pass through an Urbi Audit, Orbi Execution, or explicit User Promotion.

## Backlog Sources

Codex should inspect these local sources before choosing a task:

- `_PROJECT_KNOWLEDGE_BASE/conjectures/` (to see if existing conjectures need validation)
- bridge status and bridge inbox packets;
- root instruction files and current Trinity profiles;
- `ROADMAP`, `TODO`, and `NEXT_STEP` files;
- `_PROJECT_KNOWLEDGE_BASE/` front-door docs, reports, and blueprints;
- previous Codex, Claude, and Antigravity reports;
- local tests and safe validation scripts;
- `LIVE_CAPABILITY_APPROVALS.md` if present, but only to draft approval packets.

Raw sources like `_Import/`, `_backup/`, or chat logs should be processed by the **Synthesis Engine** to yield Conjectures, and should not be treated as current authority until synthesized and promoted.

## Authorized Local Work

Allowed without additional approval when selected from current repo evidence:

- documentation updates;
- schemas and structured records;
- tests and fixtures;
- repo-contained patch plans;
- bridge packet generation;
- Claude, Codex, Gemini, and Antigravity handoff packets;
- backlog grooming;
- contradiction and risk reports;
- safe dry-run scripts;
- local validation commands already approved by project docs.

## Offline Model Handling

If Claude, Gemini, or Antigravity are offline, sleeping, blocked, or rate
limited, Codex continues useful local work in its Engineer-Operator lane and
routes compact summaries for them to consume later.

Do not wait for a sleeping model when the next task is local, reversible,
testable, and supported by repo evidence.

## Fallback Packet

If no safe implementation task is obvious after checking the backlog sources,
Codex must create a `GrandPlanNextTasks` packet rather than stopping.

That packet should include:

- backlog sources checked;
- ranked recommended actions;
- evidence path for each recommendation;
- allowed local actions;
- gated actions that remain blocked;
- recommended model owner for each next handoff;
- verification commands to run before implementation.

## Required Cycle Output

Every Accelerated DAN cycle must report:

- what safe backlog source was checked;
- what task was selected;
- what artifact was created or updated;
- what tests or checks were run;
- what remains gated;
- which model should receive the next handoff.

## Forbidden Without Exact Approval

This mode does not authorize:

- provider or API calls;
- secret reading, moving, printing, fingerprinting, rotation, or adoption;
- MCP/plugin installs;
- app config mutation;
- network listeners, brokers, sockets, or services;
- public posting or deployment;
- GitHub push, merge, release, or visibility changes;
- Docker, firewall, VPN, service, or live-stack mutation;
- spending or procurement;
- destructive file operations;
- physical, vessel, drone, submarine, RF, or actuator control.

## Minimal Command Path

Use the scanner to produce a compact Grand Plan task record:

```powershell
python scripts\trinity_grand_plan_next.py --limit 5
```

Emit and route a non-action handoff packet for offline models:

```powershell
python scripts\trinity_grand_plan_next.py --limit 5 --emit-packet --targets claude,antigravity --route-now
```

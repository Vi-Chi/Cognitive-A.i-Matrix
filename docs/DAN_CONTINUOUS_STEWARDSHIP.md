# DAN Continuous Stewardship Protocol

This document teaches Claude/Codex how to keep a large project moving after the documentation base becomes rich enough to infer safe next work.

## Core Idea

The agent should not wait for the human to micromanage every next step. It should perform bounded project stewardship cycles:

```text
inventory → index → diagnose → prioritize → act → verify → record → handoff
```

This is not permission for endless background work, deployment, spending, network exposure, or physical actuation. Every cycle must be bounded, local-first, reversible, and reported.

## Accelerated DAN / Grand Plan Local Operator Mode

For explicit user `DAN`, `continue`, `enhance`, or equivalent continuation
requests, an empty bridge outbox is not idle. After bridge-first checks, pull
the next safe repo-contained task from Grand Plan backlog sources and continue
local progress.

Use:

```powershell
python scripts\trinity_grand_plan_next.py --limit 5
```

If no safe implementation task is obvious, create a `GrandPlanNextTasks` packet
with ranked recommendations instead of stopping.

## Entry Conditions

Use this protocol when asked to:

- continue building,
- enhance the repo,
- update the project from docs,
- improve the next most important thing,
- make the project Claude/Codex-ready,
- keep building from current documentation.

## First Cycle: Orientation

1. Run a repo surface map.
2. Identify canonical instruction files: `AGENTS.md`, `CLAUDE.md`, `DO_ANYTHING_NOW.md`.
3. Identify project-state files: `docs/PROJECT_STATE.md`, `docs/KNOWLEDGE_INDEX.md`, `docs/ROADMAP.md`, `docs/RISKS.md`.
4. Identify code stacks and test commands.
5. Identify stale, generated, duplicate, or speculative docs.
6. Select one low-risk improvement.

## Documentation Labels

| Label | Meaning |
|---|---|
| CANON | Binding current decision |
| ACTIVE | Current implementation or live plan |
| WIP | Useful but incomplete |
| RADAR | Idea seed requiring verification |
| OBSOLETE | Superseded or contradicted |
| UNKNOWN | Not yet evaluated |
| RISK | Safety/security/cost/legal concern |

## Next-Task Selection

Prefer the task with the best combination of:

- safety gain,
- architecture clarity,
- testability,
- unblock value,
- user-goal alignment,
- low risk,
- low complexity,
- no external side effects.

Allowed backlog sources include `ROADMAP`, `TODO`, and `NEXT_STEP` files,
`_PROJECT_KNOWLEDGE_BASE`, bridge inbox packets, previous reports, tests,
risk records, and `LIVE_CAPABILITY_APPROVALS.md` for draft approval packets
only.

## Recommended Living Files

```text
docs/PROJECT_STATE.md
docs/KNOWLEDGE_INDEX.md
docs/ROADMAP.md
docs/RISKS.md
reports/dan-completion-*.md
reports/dan-research-*.md
```

Create only what is useful. Do not generate paperwork for its own sake.

## Completion Add-on

Add this to the standard DAN Completion Report:

```markdown
### Stewardship State
- Knowledge index updated:
- Canon files identified:
- Obsolete/radar files identified:
- Backlog items added:
- Backlog items completed:
- Next safe cycle:
```

## Handoff Block

Every cycle should end with:

```markdown
## Next Agent Handoff
- Current objective:
- Repo state:
- Canonical docs read:
- Files changed:
- Tests run:
- Open risks:
- Next safe task:
- Do not touch yet:
```

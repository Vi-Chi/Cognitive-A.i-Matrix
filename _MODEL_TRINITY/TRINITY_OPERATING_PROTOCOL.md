# Trinity Operating Protocol

## Cycle

1. Scout/build - Antigravity explores or scaffolds.
2. Audit/synthesize - Claude reviews, critiques, and documents.
3. Patch/verify - Codex implements bounded patches and runs checks.
4. Record - outputs become records, reports, or proposal files.
5. Gate - MΣBUS, Urbi, Orbi, and the user decide promotion where applicable.
6. Preserve divergence - unresolved disagreements remain `[=]` records.

## Foreground Automation

The local Trinity+DAN cycle runner may automate a bounded workspace cycle:

```text
arbitrate outbox packets -> route safe bridge packets -> process safe execution
requests -> run optional DAN checks -> write cycle ledger/state -> optionally
post cycle_summary packets
```

This is foreground repo-local automation only. It does not install hooks,
configure MCP servers, mutate app settings, call models, or become a hidden
service.

The arbitrator is a Membrane-style queue discipline layer: it classifies
records, writes compact deltas and claim locks, and quarantines unresolved
packets. It does not decide truth, execute actions, or replace Urbi/Orbi/MΣBUS
promotion gates.

## Offline Continuation

When the user explicitly invokes DAN, continue, enhance, or equivalent
continuation language and the bridge has no queued packets, Codex should not
stop after reporting that Claude or Antigravity are offline. Codex should carry
the grand plan inside its Engineer-Operator lane by running Accelerated DAN /
Grand Plan Local Operator Mode.

The continuation order is:

1. Prefer real bridge packets and handoffs.
2. If no packets exist, read current state, reports, risks, tests, and active
   handoff docs.
3. Pick the highest-value safe local task from evidence.
4. Implement the smallest reversible improvement.
5. Verify locally.
6. Leave compact bridge packets or reports for Claude and Antigravity to audit
   when they wake.
7. If no safe implementation task is obvious, create a `GrandPlanNextTasks`
   packet with ranked recommendations.

Passive heartbeat checks are different: without a new packet or actionable
signal, they should stay quiet and avoid repo mutation.

Detailed policy: `_MODEL_TRINITY/GRAND_PLAN_LOCAL_OPERATOR_MODE.md`.

## Direct Reconfiguration

Allowed inside `_MODEL_TRINITY/` and root agent instruction files only.

Every direct cross-model reconfiguration must:

- be visible in a diff or backup comparison;
- update `CONFIG_CHANGE_LOG.md`;
- include a rollback note;
- preserve the target model's specialty;
- avoid granting unrestricted authority;
- avoid weakening project law.

## Promotion

Workbench configuration may evolve quickly. Canonical law changes require
explicit user approval and must preserve:

- Urbi audits;
- Orbi acts;
- MΣBUS gates as Membrane authority layer;
- the user as final promotion authority.

## Default Stop Gates

Do not cross these gates through Trinity workflow files:

- required paid API keys;
- live deployment;
- public posting;
- service connector writes;
- MCP/plugin installation;
- unrestricted shell or Docker access;
- credentials or secrets;
- live physical, vessel, drone, or actuator control.

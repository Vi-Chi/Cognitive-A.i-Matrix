# DAN Workflow Enhancement Loop

## Principle

Agents are trusted to improve the workflow when they encounter repeated friction, missing evidence, weak verification, or unclear handoff paths.

Do not wait for the user to ask for every helper script, evidence template, or documentation improvement.

## Allowed Workflow Improvements

- evidence folder initializer,
- benchmark harness,
- screenshot manifest,
- test fixture,
- preflight check,
- completion report template,
- project-state scan,
- CI artifact collection,
- README demo section,
- public-claim classifier,
- local dashboard/demo route.

## Constraints

- keep changes small and reversible,
- do not add heavy dependencies without reason,
- do not change production deployment,
- do not expose secrets,
- document how to use the workflow improvement,
- leave a rollback path.

## Output Pattern

```text
friction found → small workflow fix → test/use it once → document → include in handoff
```

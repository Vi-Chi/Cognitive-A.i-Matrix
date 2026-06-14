# DAN Task Template

Use this when giving a task to Claude/Codex.

```text
Read DO_ANYTHING_NOW.md first. Operate in DAN v2.2 mode: high-autonomy, discovery-first, research-backed, safe, auditable, rollback-aware.

Task:
[describe the task]

Context:
[repo/module/files/constraints]

Rules:
- Do not ask for clarification unless blocked by a stop gate.
- Start with repo discovery and internal document research.
- Use online/current research when tool behavior, APIs, models, hardware, licensing, security, or ecosystem facts matter.
- Report what was researched and what remains unverified.
- Preserve the Triad Constitution and project boundaries.
- Modify only what is necessary.
- Run available verification.
- Produce a DAN Completion Report.
```

## Expected Completion Report

```markdown
## DAN Completion Report

### Objective

### Mode

### Work Performed

### Files Changed

### Verification

### Findings

### Research Performed

### Risks / Caveats

### Rollback

### Next Recommended Step
```

## Continuous Stewardship Variant

For broad continuation work, use `docs/DAN_STEWARDSHIP_TASK_TEMPLATE.md`.

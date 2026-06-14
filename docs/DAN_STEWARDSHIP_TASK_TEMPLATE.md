# DAN Stewardship Task Prompt

Use this when asking Claude/Codex to continue a mature project without micromanagement.

```text
Read DO_ANYTHING_NOW.md first. Operate in DAN v2.2 Continuous Stewardship Mode.

Goal:
Keep building and improving this project from the existing documentation and codebase.

Rules:
- Do not ask for clarification unless a stop gate blocks safe progress.
- First inventory and index the repository documentation.
- Classify docs as CANON / ACTIVE / WIP / RADAR / OBSOLETE / UNKNOWN / RISK.
- Identify contradictions, missing tests, stale docs, weak interfaces, and safety gaps.
- Pick the next safe, high-value, reversible task.
- Implement one bounded improvement cycle.
- Run available verification.
- Update project-state docs or roadmap when useful.
- Do not deploy, spend, push, expose networks, rotate credentials, delete important files, or actuate hardware without explicit approval.
- End with a DAN Completion Report and Next Agent Handoff.
```

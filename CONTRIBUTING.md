# Contributing

Project Autopoiesis is private during Phase 0. Contributions must preserve the
project boundary and the default simulation posture.

## Required Checks

Before a change lands:

```powershell
python scripts/validate_project.py
```

## Contribution Rules

- Keep Omni-AI, Cognitive Matrix, SigmaBUS, and Autopoiesis responsibilities
  separate.
- Add chain or decentralized compute components only when their role is stated
  and testable.
- Keep private memory and local service details out of public or remote
  workflows.
- Document rollback and audit behavior for any prototype that changes state.
- Prefer local JSON or SQLite simulation before any live network integration.

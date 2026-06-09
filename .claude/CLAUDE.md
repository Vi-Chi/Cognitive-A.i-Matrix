# cognitive-matrix-proto — Claude Code Project

**Read AGENTS.md first — it is the authoritative agent instruction file.**

## Quick Reference

Skills live in `skills/` (pull from Google Drive for latest — Vi edits there).
Implementations go in `src/cm/<module_name>/`.
Tests go in `tests/`.
Specs go in `specs/`.

## Drive Skill Files (always pull latest)

Google Drive folder: `cognitive-matrix-proto/` (digivichi@gmail.com)
All 6 skill files + cm_architecture.md + module-contracts.md are there.
Vi edits Drive directly — do not assume repo = Drive.

## Working Rules

- Implement one module at a time, test before moving on
- All code: Python 3.11+, fully typed, no torch/tensorflow/GPU deps
- Adversarial tests required for every module
- Update specs/module-contracts.md before implementing any new module interface
- Use Sigma Bus for all inter-module communication

## Current Phase

Phase 1: GSS (Geometric State Space) implementation + tests
Block: Do not start BRE until GSS passes all adversarial tests

# Cognitive Matrix — Prototype

Autonomous cognitive architecture for maritime edge AI.

**Platform:** Raspberry Pi 5 (8GB) + Hailo-10H NPU
**Vessel:** Vento-Vivere (Wibo 835)
**Owner:** ViChi

## Design Principles

- Non-anthropomorphic — does not simulate human cognition
- Edge-deployable — no GPU, no cloud inference required
- Sigma Bus typed message protocol — no direct module coupling
- Friston FEP grounded — free energy minimization drives decisions
- Maritime-hardened — sensor dropout, GPS denial, power fluctuation, storm mode

## Repo Structure

```
cognitive-matrix-proto/
├── AGENTS.md              ← agent instructions (read this first)
├── specs/                 ← architecture specs and module contracts
├── skills/                ← per-module skill files (Claude Code loads on demand)
│   ├── gss/SKILL.md
│   ├── sigma-bus/SKILL.md
│   ├── bre/SKILL.md
│   ├── dream-layer/SKILL.md
│   ├── arbitration/SKILL.md
│   └── pattern-agents/SKILL.md
├── src/
│   └── cm/               ← validated module implementations
│       ├── gss/
│       ├── cgm/
│       ├── bre/
│       ├── cal/
│       ├── cap/
│       ├── smc/
│       └── inv/
└── tests/                 ← adversarial test cases
```

## Skills Source

Module skill files are maintained in Google Drive (`cognitive-matrix-proto/` folder, digivichi@gmail.com).
Pull latest before implementing — Vi edits Drive directly.

## Getting Started

See `AGENTS.md` for full agent instructions.
For Claude Code sessions: open this folder, skills auto-load based on task.

## Safety

This system is advisory-only. No LLM has write authority to vessel helm,
collision-avoidance, battery protection, or any safety interlock.

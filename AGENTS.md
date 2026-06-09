# Cognitive Matrix (CM) — Agent Instructions

## Project Identity

Cognitive Matrix is an autonomous cognitive architecture for maritime edge AI.
It is not anthropomorphic. It does not simulate human cognition. It is an
engineering system that produces correct, reliable, edge-deployable behaviour
under real-world maritime constraints.

Project: cognitive-matrix-proto
Platform: Raspberry Pi 5 (8GB) + Hailo-10H NPU (M.2 2280)
Context: Maritime autonomous navigation — Wibo 835 sailing vessel
Language: Python 3.11+, fully typed
Constraints: No GPU dependencies. No torch. No tensorflow. No cloud inference.
All modules must run on constrained edge hardware within thermal and power budgets.

---

## Architecture Overview

### Foundational substrate
The Geometric State Space (GSS) is the canonical ground truth for all system state.
All modules read from and write to the GSS via the Sigma Bus. No module communicates
with another module directly — all inter-module communication is message-passing
through the Sigma Bus using the typed six-field protocol.

### Seven core modules
| ID | Name | Role |
|----|------|------|
| GSS | Geometric State Space | Manifold-based canonical state representation |
| CGM | Cognitive Graph Manager | Knowledge graph and relational memory management |
| BRE | Behavior Reasoning Engine | Decision logic, action ranking under uncertainty |
| CAL | Context Awareness Layer | Environmental and situational context fusion |
| CAP | Cognitive Action Processor | Action execution and feedback integration |
| SMC | State Monitor Controller | Health monitoring, fault detection, mode control |
| INV | Invariant Validator | Architectural constraint enforcement and integrity checks |

### Eight capability modules (Greek notation)
ΦP — Perception, ΦM — Memory, ΦR — Reasoning, ΦA — Action
ΦL — Learning, ΦC — Communication, ΦS — Self-monitoring, ΦΩ — Meta-cognition

### Dream layer
ΦΔ — offline coherence engine with five sub-engines, runs in DREAM state only

### Arbitration layer
ΦΨ — State Arbitration Layer, governs tri-state transitions: WAKE / LIMINAL / DREAM

### Pattern recognition agents (bidirectional, FEP-grounded)
Φ_COR — Correlation, Φ_STA — Statistical, Φ_DIS — Distributional
Φ_STR — Structural, Φ_LEA — Learning/Adaptive

### Memory tiers
T₀ — Working (in-session, fast access)
T₁ — Episodic (recent events, indexed by time and context)
T₂ — Semantic (consolidated knowledge, concept graphs)
T₃ — Archival (compressed long-term storage, dream-consolidated)

---

## Sigma Bus Protocol

All inter-module messages use the typed six-field protocol:
M := (v, σ, π, δ, κ, τ)

- v — schema version (int)
- σ — source module ID (string, e.g. "GSS", "BRE", "ΦΔ")
- π — priority level (int, 0=background, 1=normal, 2=elevated, 3=critical)
- δ — payload (typed dict, module-specific schema)
- κ — context flags (list of strings, e.g. ["LIMINAL", "SENSOR_DEGRADED"])
- τ — timestamp (ISO8601, UTC)

The Sigma Bus is not a network — it is a typed in-process message protocol.
No external broker. No serialisation to disk unless archiving.

---

## Agent Rules

1. Never invent module interfaces not specified in specs/module-contracts.md
2. All code must run on Python 3.11+ with no GPU-only dependencies
3. Every implementation must include adversarial test cases (not just happy path)
4. Commit each validated module to src/cm/<module_name>/
5. Use Sigma Bus for all inter-module communication — never direct function calls across module boundaries
6. When modifying a module contract, update specs/module-contracts.md first, then implement
7. Flag any assumption that could fail under maritime conditions (sensor dropout, GPS denial, extreme weather, power fluctuation)
8. Output format: implementation code first, then interface contract summary, then failure modes. No prose padding.

---

## Available Skills

| Skill directory | Trigger conditions |
|----------------|-------------------|
| skills/gss/ | Any task involving state vectors, manifold operations, GSS reads/writes |
| skills/sigma-bus/ | Any task involving inter-module messaging, protocol validation |
| skills/bre/ | Any task involving decision logic, action ranking, uncertainty handling |
| skills/dream-layer/ | Any task involving ΦΔ, DREAM state, coherence engine, memory consolidation |
| skills/arbitration/ | Any task involving ΦΨ, state transitions, WAKE/LIMINAL/DREAM arbitration |
| skills/pattern-agents/ | Any task involving Φ_COR/STA/DIS/STR/LEA, FEP loops, prediction error |

---

## Current Prototype Phase

Phase 1 — Schema validation and GSS implementation
Status: IN PROGRESS
Next: Implement GSS state vector with manifold ops and adversarial tests

Do not skip phases. Each phase validates the foundations the next phase builds on.

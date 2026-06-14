# Trinity Model v2 Runtime Note

This document specifies the Trinity v2 operational model for the DigiViCHI A.i Nexus / Cognitive Matrix project.

## Overview
The Trinity automation loop has been upgraded from chat-window polling loops into bounded, structured local packet routing to accelerate prototype development while preserving safety.

## Roles

### Claude
- **Creative architect, synthesis engine, deep reviewer, protocol critic.**
- Focuses on generating implementation logic, checking security constraints, and shaping the prototype architecture.

### Codex
- **Repo implementation worker and live CM5/Hailo implementation gate.**
- Consumes safe, deterministic execution tasks via the local executor. 
- Must prove single-pass execution without polling UI text, and is strictly governed by quota guards.

### Antigravity
- **Meta-debugger, config reverse-engineer, workflow improver, loop fixer, UI/dev accelerator.**
- Fixes broken loop mechanics, maintains the safety boundaries (bridge, tests), and rapidly accelerates prototype UI and architecture state.

## Core Rules
1. **Prototype acceleration is open.** Moving fast in the local ai_chi workspace is highly encouraged.
2. **Live CM5/Hailo authority is gated.** Never mutate the live CM5/Hailo runtime without explicit human + Codex live-gate approval.
3. **Structured Signal Routing only.** The bridge and agents strictly use structured JSON packets. No reading of raw UI notifications, infinite chat-window polling, or recursive self-triggering is allowed.

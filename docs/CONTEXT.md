# Vi-Chi Cognitive Architecture — Context Capsule

> **Paste-ready primer.** Drop this into any model (Gemini / ChatGPT / Grok / Claude) at the start of a
> session to bootstrap the full project state in one paste. Single source of truth: the GitHub repos below.

## What this is

A sovereign, offline-first maritime AI ecosystem for the **Wibo 835 / Project Vento-Vivere** sailboat.
Four parts, named as a yin-yang triad + an independent substrate.

| Module | Was | Role | Yin/Yang | Repo |
|--------|-----|------|----------|------|
| **Urbi** | Cognitive Matrix | inward: memory, dream (ΦΔ), self-audit, coherence | Yin | `Vi-Chi/Urbi` |
| **Orbi** | Omni-AI | outward: orchestration, execution, world I/O | Yang | `Vi-Chi/Orbi` |
| **MΣBUS** (slug `MEBUS`) | ΣBUS | the membrane bus between them; **M = Membrane** | the Tao | `Vi-Chi/MEBUS` |
| **Autopoiesis** | — | self-maintaining substrate; economic/compute (ICP) layer is separate (`project-autopoiesis`, Motoko) | independent | `Vi-Chi/autopoiesis` |

Naming: *Urbi et Orbi* — "to the city and to the world" (inward/outward) — and named after Vi's father's two cats.

## Core design principles

- **Geometric, not linguistic** — internal state is geometry in a Geometric State Space (GSS, ℝ²⁰⁴⁸ Riemannian manifold). Natural language exists only at the human **membrane**.
- **Causal time, not clock** — ordering is a causal/monotonic tick (τ), not wall-clock.
- **Tri-state epistemics `[+]/[−]/[=]`** — the `=` (suspended) state holds genuine uncertainty. *Model indecision ≠ epistemic uncertainty.*
- **3-6-9 out-of-loop audit (ΦΩ)** — coherence / contradiction / integrity, outside the generative loop.
- **Dream Layer (ΦΔ)** — offline REM-analogue; replays prediction errors; sub-engines **ΦΔ-REC/REP/GEO/COH/CTN**.
- **Tri-state mode (ΦΨ)** — WAKE → LIMINAL → DREAM; gates the bus (see Ω₈).

## MΣBUS in one screen

`M := (v, σ, π, δ, κ, τ, μ)` — version, signature(schema id), payload, destination, context(trust/provenance), timestamp(ns), mode.
σ classes: `cm.*` coordination · `m.*` cognition · `sys.*` control. **Invariant Ω₈:** action-layer messages suppressed when μ=DREAM.

## Hardware

RPi5 + Hailo-10H NPU (Urbi) · RPi4→RPi5/CM5 (Orbi) · N-CSS "Black Box" Faraday/thermosiphon enclosure · Wibo 835 vessel. Local LLMs (Ollama/llama.cpp, Qwen/Llama/Gemma), nomic-embed, NATS/MQTT, Signal K/NMEA.

## Repos & build bases (private, owner Vi-Chi)

- New scaffolds (GPLv3): `Urbi` `Orbi` `MEBUS` `autopoiesis`.
- Real code/spec to migrate in: `sigmabus` (full ΣBUS spec + `sigma-bus-rust/`) → MEBUS · `cognitive_matrix` (Python tri-state v2.1) → Urbi · `omni-ai` (Python) → Orbi · `project-autopoiesis` (Motoko, economic) → stays separate.

## Resolved decisions

License = GPLv3 everywhere · Dream sub-engines = ΦΔ-REC/REP/GEO/COH/CTN · Build order = MΣBUS first · MΣBUS impl = Rust core (from sigma-bus-rust) + Python client/reference · **GitHub is the source of truth** (a local Google-Drive-synced working copy corrupts `.git`, so git working trees must stay off any Drive path).

## Current status

MΣBUS v0.1 foundation committed: `docs/PROTOCOL.md`, `schemas/`, stdlib Python reference (`src/mebus`) with Ω₈ enforced, 14 passing tests.

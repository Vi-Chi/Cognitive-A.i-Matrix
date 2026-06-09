# Vi-Chi Cognitive Architecture — Context Capsule

A sovereign, offline-first maritime AI ecosystem for the **Wibo 835 / Project Vento-Vivere** sailboat.

| Module | Was | Role | Yin/Yang | Repo |
|--------|-----|------|----------|------|
| **Urbi** | Cognitive Matrix | inward: memory, dream (ΦΔ), self-audit, coherence | Yin | `Vi-Chi/Urbi` |
| **Orbi** | Omni-AI | outward: orchestration, execution, world I/O | Yang | `Vi-Chi/Orbi` |
| **MΣBUS** (`MEBUS`) | ΣBUS | universal transport/transformer/gateway/translator; Membrane(Sigma + EBUS) | the Tao | `Vi-Chi/MEBUS` |
| **Autopoiesis** | — | self-maintaining polyglot substrate: watchdog, recovery + the Rust hot-path, ICP canisters, GPU networks | independent | `Vi-Chi/autopoiesis` |

## Core design principles

- **Geometric, not linguistic** — internal state is geometry (GSS, ℝ²⁰⁴⁸); language only at the human membrane.
- **Causal time, not clock** — ordering is a monotonic/causal tick (τ).
- **Tri-state epistemics `[+]/[−]/[=]`** — `=` holds genuine uncertainty. *Model indecision ≠ epistemic uncertainty.*
- **3-6-9 out-of-loop audit (ΦΩ)** · **Dream Layer (ΦΔ)** REC/REP/GEO/COH/CTN · **mode (ΦΨ)** WAKE→LIMINAL→DREAM.
- **Provenance mandatory; external models are providers, not oracles.**

## Resolved decisions

GPLv3 everywhere · build MEBUS first · Urbi/Orbi/MΣBUS = Python · Autopoiesis = polyglot (Motoko-preferred + Rust) ·
**GitHub is the source of truth** (a Drive-synced working copy corrupts `.git`; keep git trees off Drive).

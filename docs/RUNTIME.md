# Autopoiesis — Language & Runtime (polyglot open substrate)

> Architecture decision (confirmed): **Autopoiesis is the substrate — the performance floor the rest
> of the system stands on.** It is deliberately **polyglot and open**, not tied to one language.

Urbi, Orbi, and MΣBUS are **Python** (protocol logic, cognition, orchestration). The systems-level,
performance- and safety-critical runtime lives **here**, in Autopoiesis — across several platforms.

## Language policy

| Concern | Language | Why |
|---------|----------|-----|
| ICP canisters / public coordination | **Motoko (preferred)** | Open architecture, ICP-native, simple auditable actors |
| Canisters needing performance / complex data structures | **Rust** | Performance, safety, strong ICP ecosystem |
| GPU / decentralized compute networks | **Rust** | Throughput, memory safety on the hot path |
| MΣBUS transport hot-path | **Rust** (`sigma-bus-rust`) | Low-latency message routing under the Python protocol |
| Future platforms | **expanding** | The substrate is designed to grow to more runtimes/targets over time |

**Preference:** Motoko for its open architecture where it fits; Rust where performance, safety, or GPU
/ complex data structures demand it. This list is expected to **expand to more platforms** as the
system grows.

## What Autopoiesis hosts

1. **MΣBUS transport runtime (the hot path).** MΣBUS *defines* the protocol and translation
   (`M := (v, σ, π, δ, κ, τ, μ)`, Ω₈, adapters) with a Python reference. The high-throughput
   transport runtime runs here in Rust — build base: `sigma-bus-rust` (migrating in from
   `Vi-Chi/sigmabus`). **MΣBUS defines and translates; Autopoiesis runs it fast.**
2. **ICP economic canisters** — provider registry, job ledger, treasury accounting. Motoko preferred;
   Rust where needed. (`Vi-Chi/project-autopoiesis` folds in here.)
3. **GPU / decentralized compute networks** — procurement and execution brokerage (Akash/Golem-class),
   Rust on the performance path. Future: more platforms.

## Why here and not in the modules

Autopoiesis must not share failure modes with what it monitors, and it is the floor everything stands
on. Concentrating the systems-level runtime here keeps Urbi/Orbi/MΣBUS as clean, auditable Python
logic, while performance- and safety-critical machinery lives in one isolated, polyglot substrate that
can expand to new platforms without disturbing the cognition layers.

## Open reconciliation

- `Vi-Chi/project-autopoiesis` is currently tagged **Motoko**; the older design note said "Rust
  preferred" for canisters. Resolved by the policy above: **Motoko preferred for openness, Rust where
  performance/complexity demands** — settle per-canister when consolidating.
- `sigma-bus-rust` currently lives in `Vi-Chi/sigmabus`; migrate into this substrate.

## Summary

| Layer | Language | Where |
|-------|----------|-------|
| Urbi / Orbi / MΣBUS (protocol + translation) | Python | their repos |
| MΣBUS transport hot-path | Rust (`sigma-bus-rust`) | **Autopoiesis** |
| ICP economic canisters | Motoko-preferred / Rust | **Autopoiesis** |
| GPU / compute networks | Rust | **Autopoiesis** |
| Future targets | expanding | **Autopoiesis** |

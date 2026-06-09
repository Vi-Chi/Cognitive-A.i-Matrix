# Vi-Chi Cognitive Architecture

> *Urbi et Orbi* — To the city and to the world.

```
        [ World / Environment ]  Sensors · APIs · Comms · Maritime
                    │
                  ORBI            World-facing orchestration & execution (was Omni-AI)
                    │
                  MΣBUS           Membrane Sigma Bus — M(v,σ,π,δ,κ,τ,μ), Invariant Ω₈
            ┌───────┴────────┐
          URBI            AUTOPOIESIS
   Memory · Dream · Audit   Health · Recovery · Boot · Rust hot-path · ICP
   (was Cognitive Matrix)   (self-maintaining substrate)
```

## Components

- **Orbi** — active execution / world I/O (Yang). Formerly Omni-AI.
- **Urbi** — inward coherence: memory, dream (ΦΔ), self-audit, belief revision (Yin). Formerly Cognitive Matrix.
  Core modules: GSS · CGM · BRE · CAL · CAP · SMC · INV.
  Dream sub-engines (ΦΔ): REC (recapitulation) · REP (void-filling) · GEO (geodesic) · COH (coherence) · CTN (containment).
  State arbitration (ΦΨ): WAKE → LIMINAL → DREAM.
- **MΣBUS** — the typed message substrate. `M := (v, σ, π, δ, κ, τ, μ)`. Ω₈ isolates the action layer in DREAM.
  Membrane adapters: maritime · embedded · industrial.
- **Autopoiesis** — self-maintaining polyglot substrate; hosts the high-performance Rust transport runtime and the ICP economic canisters.

## Hardware reference stack

| Layer | Hardware |
|-------|----------|
| Primary compute | Raspberry Pi 5 |
| Neural accelerator | Hailo-10H NPU |
| Cyberdeck | N-CSS Black Box |
| Vessel | Wibo 835 / Vento-Vivere |

## Naming

*Urbi et Orbi* — the papal blessing *to the city and to the world* (inward / outward). Named after two cats. M = Membrane.

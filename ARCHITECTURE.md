# Vi-Chi Cognitive Architecture

> *Urbi et Orbi* — To the city and to the world.

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│             [ World / Environment ]                      │
│         Sensors · APIs · Comms · Maritime                │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                      ORBI                                │
│         World-facing orchestration & execution           │
│    Real-time · Tool-use · Agent deployment · Adapters    │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                     MΣBUS                                │
│               Membrane Sigma Bus                         │
│   M(v, σ, π, δ, κ, τ, μ) — typed universal protocol     │
│       Invariant Ω₈ — action isolation / DREAM mode       │
└────────────┬─────────────────────────┬───────────────────┘
             │                         │
┌────────────▼────────────┐  ┌─────────▼───────────────────┐
│          URBI            │  │       AUTOPOIESIS            │
│  Inward coherence layer  │  │  Self-maintaining substrate  │
│ Memory · Dream · Audit   │  │  Health · Recovery · Boot    │
└──────────────────────────┘  └──────────────────────────────┘
```

## Components

### Orbi — Active Execution Layer
The world-facing orchestration system. Handles real-time decisions,
agent deployment, sensor integration, and external interfaces.
The executive function of the architecture.

**Formerly:** Omni-AI

---

### Urbi — Inward Coherence Layer
The cognitive integrity engine. Handles memory consolidation,
the dream/offline cycle (ΦΔ), self-audit, causal modelling,
and belief revision. The reflective function.

**Formerly:** Cognitive Matrix

**Core modules:** GSS · CGM · BRE · CAL · CAP · SMC · INV

**Capability matrix (Φ):** ΦP · ΦQ · ΦR · ΦS · ΦT · ΦU · ΦV · ΦΔ · ΦΨ · ΦΩ

**Dream sub-engines (ΦΔ):**

| Engine | Role |
|--------|------|
| ΦΔ-REC | Recapitulation / retroactive propagation |
| ΦΔ-REP | Generative void-filling |
| ΦΔ-GEO | Geodesic discovery / instinct compression |
| ΦΔ-COH | Global coherence monitoring |
| ΦΔ-CTN | Containment enforcement |

**State arbitration (ΦΨ):** WAKE → LIMINAL → DREAM (tri-state)

---

### MΣBUS — Membrane Sigma Bus
The typed message substrate connecting all components.
Environment-agnostic core with membrane adapters per deployment context.

**Protocol:** `M := (v, σ, π, δ, κ, τ, μ)`

| Field | Name | Description |
|-------|------|-------------|
| v | Version | Protocol version |
| σ | Signature | Message type/schema |
| π | Payload | Content |
| δ | Destination | Target module/agent |
| κ | Context | Contextual metadata |
| τ | Timestamp | Monotonic time reference |
| μ | Mode | System mode tag (WAKE/LIMINAL/DREAM) |

**Invariant Ω₈:** Action-layer isolation enforced during DREAM mode.

**Membrane adapters:** maritime · embedded · industrial

---

### Autopoiesis — Self-Maintaining Substrate
Operates independently of the Urbi/Orbi/MΣBUS triad.
Inspired by Maturana & Varela: a system is autopoietic when it
continuously produces the components that constitute it.

---

## Naming

> *"Urbi et Orbi"* — the Latin phrase spoken in the papal blessing:
> *to the city and to the world.*
>


---

## Hardware Reference Stack

| Layer | Hardware |
|-------|----------|
| Primary compute | Raspberry Pi 5 |
| Neural accelerator | Hailo-10H NPU |
| Cyberdeck | N-CSS Black Box |
| Vessel |

---

## Repository Map

| Repo | Name | Role |
|------|------|------|
| `urbi` | Urbi | Inward coherence, memory, dream, self-audit |
| `orbi` | Orbi | World-facing orchestration and execution |
| `msigmabus` | MΣBUS | Membrane Sigma Bus — typed connective substrate |
| `autopoiesis` | Autopoiesis | Self-maintaining substrate |

# MΣBUS — Membrane Sigma Bus

> The connective tissue. The medium through which Urbi and Orbi breathe.

MΣBUS is the typed message substrate connecting all components of the
Vi-Chi Cognitive Architecture. It is environment-agnostic at its core,
with deployment-specific membrane adapters for maritime, embedded,
industrial, and other contexts.

The **M** stands for **Membrane** — the selective interface layer that
is the same everywhere inside, and adapts to whatever is outside.

**Formerly:** ΣBUS / SigmaΣBUS

---

## Architecture Position

```
         ORBI
           │  (publishes / subscribes)
    ───────▼────────
         MΣBUS          ← you are here
    ───────┬────────
           │  (publishes / subscribes)
         URBI
```

---

## Universal Message Protocol

Every message on the bus conforms to the seven-field protocol:

```
M := (v, σ, π, δ, κ, τ, μ)
```

| Field | Name | Description |
|-------|------|-------------|
| v | Version | Protocol version |
| σ | Signature | Message type / schema identifier |
| π | Payload | Message content |
| δ | Destination | Target module or agent |
| κ | Context | Contextual metadata |
| τ | Timestamp | Monotonic time reference |
| μ | Mode | System mode tag (WAKE / LIMINAL / DREAM) |

---

## Invariants

| ID | Rule |
|----|------|
| Ω₈ | Action-layer messages are suppressed when μ = DREAM |

---

## Membrane Adapters

The core bus is environment-agnostic.
Adapters provide the context-specific membrane:

| Deployment | Adapter path |
|------------|-------------|
| Maritime (Vento-Vivere / Wibo 835) | `membrane/maritime` |
| Embedded (RPi5 + Hailo-10H) | `membrane/embedded` |
| Industrial | `membrane/industrial` |

---

## Related

- [Urbi](../urbi) — Inward coherence layer (subscriber / publisher)
- [Orbi](../orbi) — World-facing orchestration layer (publisher / subscriber)
- [Autopoiesis](../autopoiesis) — Self-maintaining substrate

---

*Part of the Vi-Chi Cognitive Architecture.
MΣBUS: Membrane Sigma Bus.
The M denotes the membrane architecture — same core, context-specific surface.*

---

## License

This project is licensed under the **GNU General Public License v3.0**.
See [LICENSE](LICENSE) for full terms.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
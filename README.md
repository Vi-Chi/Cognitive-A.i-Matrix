# Orbi

> *To the world.* — World-facing orchestration and active execution layer.

Orbi is the outward half of the Urbi/Orbi duality.
It handles real-time orchestration, task planning, agent deployment,
sensor integration, and all interfaces with the external environment.
Where Urbi thinks inward, Orbi projects outward.

**Formerly:** Omni-AI

---

## Architecture Position

```
[ World / Environment / Sensors / APIs ]
                   ↕
                ORBI              ← you are here
                   ↕
                MΣBUS
                   ↕
                URBI
```

---

## Core Responsibilities

- Real-time agent orchestration and task planning
- Tool-use and action execution
- External API and sensor integration
- Maritime / edge deployment membrane adapters
- Publishing to MΣBUS; subscribing to Urbi state

---

## MΣBUS Interface

Orbi publishes and subscribes on the Membrane Sigma Bus (MΣBUS).
All messages conform to the universal protocol:

```
M := (v, σ, π, δ, κ, τ, μ)
```

During `μ = DREAM`, Orbi respects invariant Ω₈:
no action-layer messages are dispatched.

---

## Hardware Targets

- Raspberry Pi 5 + Hailo-10H NPU
- N-CSS Black Box Cyberdeck
- (maritime)

---

## Related

- [Urbi](../urbi) — Inward coherence, memory, dream, self-audit
- [MΣBUS](../msigmabus) — Membrane Sigma Bus
- [Autopoiesis](../autopoiesis) — Self-maintaining substrate

---

*
Part of the Vi-Chi Cognitive Architecture.
Naming: Latin "Urbi et Orbi" — to the city and to the world.
*


---

## License

This project is licensed under the **GNU General Public License v3.0**.
See [LICENSE](LICENSE) for full terms.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
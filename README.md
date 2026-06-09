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

## Universal Message Protocol

```
M := (v, σ, π, δ, κ, τ, μ)
```

| Field | Name | Description |
|-------|------|-------------|
| v | Version | Protocol version |
| σ | Signature | Message type / schema identifier (dotted `class.name`) |
| π | Payload | Message content |
| δ | Destination | Target module or agent |
| κ | Context | Contextual metadata (trust / provenance / expiry) |
| τ | Timestamp | Monotonic nanosecond tick (ordering, not wall-clock) |
| μ | Mode | System mode tag (WAKE / LIMINAL / DREAM) |

## Invariants

| ID | Rule |
|----|------|
| Ω₈ | Action-layer messages are suppressed when μ = DREAM |

## Signature classes (σ)

| Class | Purpose |
|-------|---------|
| `cm.*`  | Coordination speech-acts (agent ↔ agent) |
| `m.*`   | Cognition state / geometry (incl. `m.prediction_record`) |
| `ext.*` | Universal carrier — ANY foreign payload, verbatim |
| `sys.*` | Bus / system control |

## Quickstart

```python
from mebus import MMessage, Mode, MembraneBus, NMEAAdapter

bus = MembraneBus()
bus.subscribe("m.state", lambda m: print(m.payload["value"]))

fix = NMEAAdapter().ingest("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A")
bus.publish(fix)          # -> {'latitude': 48.1173, 'longitude': 11.5167, 'sog_knots': 22.4, ...}
```

Run the suite:

```bash
python -m unittest discover -s tests -v
```

## Related

- [Urbi](https://github.com/Vi-Chi/Urbi) — Inward coherence layer (Cognitive Matrix)
- [Orbi](https://github.com/Vi-Chi/Orbi) — World-facing orchestration (Omni-AI)
- [Autopoiesis](https://github.com/Vi-Chi/autopoiesis) — Self-maintaining substrate (hosts the Rust hot-path)

## License

GNU General Public License v3.0 — see `LICENSE`.

# MΣBUS Adapters & Translation — "transport anything"

MΣBUS = **Membrane(Sigma + EBUS)** — a universal transport / transformer / gateway / translator.
Same core inside; a context-specific membrane surface outside.

## Carrying anything: the `ext.*` class

`ext.*` is the universal carrier — any foreign payload (NMEA, Signal K, JSON, GUI, SDR, model
output, raw bytes) crosses the bus intact, tagged with its source in `κ.provenance`, until a
translator gives it a typed form. `ext.*` is data, not action — it flows even in DREAM.

```python
from mebus import wrap_external
m = wrap_external("nmea", {"sentence": "$GPGGA,..."})   # → σ = "ext.nmea", carried verbatim
```

## Adapters

An **Adapter** is a bidirectional translator between an external format and an `MMessage`
(`ingest` outside→bus, `emit` bus→outside).

| Adapter | `ingest` → σ | Role |
|---------|-------------|------|
| `JSONAdapter`   | `ext.json` | simplest universal JSON/dict gateway |
| `SignalKAdapter`| `m.state` (domain `maritime.nav`) | Signal K delta → typed maritime cognition |
| `NMEAAdapter`   | `m.state` (GGA/RMC) / `ext.nmea` (other) | NMEA 0183 → typed position; unknown sentences carried verbatim |

An `AdapterRegistry` holds the membrane's installed translators. Deployment membranes
(maritime / embedded / industrial) are just adapter sets.

## Gateway pattern

Adapters translate both directions, so MΣBUS is a **gateway**: ingest from format A, re-`emit` to
format B. External AI providers (Nemotron/OpenAI/Claude/Grok) enter as `ext.*` / `cm.inform` with
`external_model` provenance — evidence, never sensory truth.

## Roadmap

NMEA 2000, MQTT, NATS, MCP tool calls, A2A, SDR/SigMF, GUI/UI-automation state, files/logs,
vector/embedding state. Each is an `Adapter`; none changes the core.

# MΣBUS Protocol — v0.1 (canonical)

> **MΣBUS = Membrane(Sigma + EBUS).** A universal **transport / transformer / gateway / translator**
> between **Orbi** (outward) and **Urbi** (inward) — not merely a message bus. Environment-agnostic
> core; context-specific membrane adapters. Supersedes ΣBUS / SigmaΣBUS. License: GPL-3.0-or-later.

## 1. The seven fields — `M := (v, σ, π, δ, κ, τ, μ)`

| Field | Name | Type | Meaning |
|------|------|------|---------|
| v | version | int | Protocol schema version (currently `1`). |
| σ | signature | str | Payload schema / message-type id, dotted `class.name`. Drives routing **and** payload dispatch. |
| π | payload | object | Message content. Schema determined by σ. |
| δ | destination | str | Target module / agent / path. |
| κ | context | object | Metadata — trust, provenance, expiry (the ΣBUS-CM Semantic Envelope). |
| τ | timestamp | int | Monotonic **nanoseconds**. Ordering, not wall-clock. |
| μ | mode | enum | System mode: `WAKE` \| `LIMINAL` \| `DREAM`. |

## 2. Signature classes (σ) — one wire, four payload families

| Class | Purpose | Examples |
|-------|---------|----------|
| `cm.*` | Coordination speech-acts | announce, heartbeat, query, inform, request, confirm, fail, propose, agree, refuse, retract, delegate, resume, alert, withdraw |
| `m.*` | Cognition state/geometry | `m.state` `m.prediction_record` `m.belief` `m.action` |
| `ext.*` | Universal carrier — ANY foreign payload, verbatim | `ext.nmea` `ext.signalk` `ext.json` `ext.sdr` `ext.gui` `ext.model` |
| `sys.*` | Bus / system control | `sys.mode` `sys.health` |

## 3. Invariant Ω₈ — mode-gated routing

| μ | Sensory (in) | Action (out) |
|---|--------------|--------------|
| **WAKE** | open | open |
| **LIMINAL** | reduced | held / advisory |
| **DREAM** | gated (monitor) | **SUPPRESSED** |

**Ω₈ (hard invariant):** when `μ = DREAM`, any σ in the action layer is suppressed (audited, not
delivered). Action layer = `cm.request, cm.confirm, cm.fail, cm.propose, cm.agree, cm.refuse,
cm.retract, cm.delegate, cm.resume, m.action`, and any `cmd.*` path. Cognition (`m.*`), information
(`cm.inform`, `cm.alert`) and carried data (`ext.*`) still flow so consolidation can proceed.

## 4. Context (κ) — trust, provenance, freshness

`κ` carries the ΣBUS-CM Semantic Envelope: `trust_score` (0–1), `anomaly_score`, `cross_validated`,
`provenance`, `t_expires` (ns). **Effective trust:**
`clamp(base − age_decay(Δτ) − anomaly·0.5 + (0.1 if cross_validated), 0, 1)`; below `0.1` → discard.

## 5. Transport & runtime

Transport-agnostic. Reference bindings: **NATS JetStream** (primary/persistent/federated), **ZeroMQ**
(intra-platform low-latency), **MQTT** (IoT/maritime), **serial/HF** (bandwidth-constrained).
MΣBUS owns protocol + translation; the **Rust transport hot-path is hosted by Autopoiesis**.

## 6. Conformance levels

- **L1 Minimal** — envelope + validation + `cm.announce/withdraw/heartbeat/query/inform`.
- **L2 Standard** — + action/negotiation/alert + Ω₈ + conversation state.
- **L3 Gateway** — + delegate/resume + federation + store-and-forward + multi-format adapters.

## 7. Status

v0.1 foundation: Python reference + adapter/translation layer + Ω₈ + PredictionRecord synapse.
This local build adds the **NMEA 0183 adapter**, the **m.* cognition payload** (cognition.py), and
the **cm.* coordination layer** (AID + 15 message types + negotiation; coordination.py). Next: ed25519
via sigma-bus-rust, conformance asserts, and wire serialisation (NATS/MQTT/ZeroMQ).
adapters, the `cm.*` payload schemas, and wiring to the Autopoiesis-hosted Rust runtime.

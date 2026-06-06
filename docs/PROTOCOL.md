# MΣBUS Protocol — v0.1 (canonical)

> **MΣBUS = Membrane Sigma Bus.** The typed message substrate between **Orbi** (outward) and **Urbi**
> (inward). Environment-agnostic core; context-specific membrane adapters. Supersedes ΣBUS / SigmaΣBUS.
> License: GPL-3.0-or-later.

This spec **reconciles three earlier message definitions** into one:
1. the MΣBUS repo frame `M := (v, σ, π, δ, κ, τ, μ)` (the outer envelope — canonical here);
2. the ΣBUS-CM Semantic Envelope + AID (rich coordination/trust/provenance detail — lives in `κ` and in `cm.*` payloads);
3. the geometric M-tuple (cognition/state — lives in `m.*` payloads).

---

## 1. The seven fields

`M := (v, σ, π, δ, κ, τ, μ)`

| Field | Name | Type | Meaning |
|------|------|------|---------|
| v | version | int | Protocol schema version (currently `1`). |
| σ | signature | str | Payload schema / message-type id, dotted `class.name` (e.g. `cm.propose`, `m.prediction_record`). Drives routing **and** payload dispatch. |
| π | payload | object | Message content. Schema determined by σ. |
| δ | destination | str | Target module / agent / path (e.g. `urbi`, `orbi`, `cm.wibo835.broadcast`, `cmd.autopilot.heading`). |
| κ | context | object | Contextual metadata — trust, provenance, expiry. This is where the **ΣBUS-CM Semantic Envelope** lives (trust_score, provenance chain, t_expires, anomaly_score). |
| τ | timestamp | int | Monotonic reference in **nanoseconds**. Ordering, not wall-clock. |
| μ | mode | enum | System mode: `WAKE` \| `LIMINAL` \| `DREAM`. |

---

## 2. Signature namespaces (σ) — the two-bus reconciliation

σ is `class.name`. The class selects the payload family, unifying the two historical buses on one wire:

| Class | Purpose | Examples | Source design |
|-------|---------|----------|---------------|
| `cm.*` | **Coordination** speech-acts (agent↔agent) | `cm.announce` `cm.heartbeat` `cm.query` `cm.inform` `cm.request` `cm.confirm` `cm.fail` `cm.propose` `cm.agree` `cm.refuse` `cm.retract` `cm.delegate` `cm.resume` `cm.alert` `cm.withdraw` | ΣBUS-CM spec (FIPA-ACL lineage) |
| `m.*` | **Cognition** state/geometry | `m.state` `m.prediction_record` `m.belief` `m.action` | geometric M-tuple / Dream Layer |
| `sys.*` | **Bus / system** control | `sys.mode` `sys.health` | MΣBUS itself |

`cm.*` payloads carry the ΣBUS-CM message bodies; `κ` carries their Semantic Envelope (trust/provenance).
`m.prediction_record` is the **cognition synapse** — emitted in WAKE, consumed by the Urbi Dream Layer (ΦΔ).

---

## 3. Invariant Ω₈ — mode-gated routing

`μ` is not a passive tag; it **gates the bus**. The membrane behaves differently per mode:

| μ | Sensory (in) | Action (out) | Notes |
|---|--------------|--------------|-------|
| **WAKE** | open | open | Full traffic, all σ classes. |
| **LIMINAL** | reduced | held / advisory | Delivered but flagged advisory; T₁-fast instinct watchdog. |
| **DREAM** | gated (monitor) | **SUPPRESSED** | **Ω₈: action-layer messages MUST NOT be delivered.** |

**Ω₈ (hard invariant):** when `μ = DREAM`, any message whose σ is in the **action layer** is suppressed
(never reaches handlers; recorded in the audit log). The action layer = `cm.request, cm.confirm, cm.fail,
cm.propose, cm.agree, cm.refuse, cm.retract, cm.delegate, cm.resume, m.action`, and any `cmd.*` path.
This prevents the Dream Layer from actuating the world. Cognition (`m.*`) and information (`cm.inform`,
`cm.alert`) still flow so consolidation can proceed.

---

## 4. Context (κ) — trust, provenance, freshness

`κ` carries the load-bearing metadata from the ΣBUS-CM Semantic Envelope:

- `trust_score` (0–1), `anomaly_score` (0–1), `cross_validated` (bool)
- `provenance` — derivation/source chain (every value traceable to ground truth)
- `t_expires` (ns) — after which the value is stale and MUST NOT be acted upon

**Effective trust** (from ΣBUS-CM): `clamp(base − age_decay(Δτ) − anomaly·0.5 + (0.1 if cross_validated), 0, 1)`;
messages below `0.1` MUST be discarded. (Per-σ age half-lives defined in the ΣBUS-CM spec.)

---

## 5. Transport, runtime & the Autopoiesis substrate

MΣBUS is transport-agnostic. Reference bindings (from ΣBUS-CM §13):

| Transport | Use | Notes |
|-----------|-----|-------|
| **NATS JetStream** | primary / persistent / federated | embedded server <50 MB RAM on RPi5 |
| **ZeroMQ** | intra-platform low-latency `m.*` | PUB/SUB + DEALER/ROUTER |
| **MQTT** | IoT / maritime compatibility | QoS 1 for `cm.*` |
| **Serial / HF** | bandwidth-constrained | zstd + binary; only `cm.alert`/`cm.propose` cross by default |

**Division of labour (architecture decision):** MΣBUS owns the *protocol* — the seven-field envelope,
σ dispatch, Ω₈ semantics, schemas. The reference implementation (`src/mebus`) is **Python**: an
in-process bus for development and tests and the canonical home of the protocol logic. The
**high-performance Rust transport runtime is provided by the Autopoiesis substrate** — Autopoiesis is the
systems-level "floor" that hosts the hot-path bus runtime (the `sigma-bus-rust` core migrates there from
`Vi-Chi/sigmabus`) alongside the ICP economic canisters. **MΣBUS defines the protocol; Autopoiesis runs
it fast.**

---

## 6. Conformance (reference levels, from ΣBUS-CM)

- **L1 Minimal** — envelope + validation + `cm.announce/withdraw/heartbeat/query/inform`.
- **L2 Standard** — + action/negotiation/alert + Ω₈ mode-gating + conversation state.
- **L3 Gateway** — + delegate/resume + federation + store-and-forward.

This v0.1 implements the envelope, validation, and **Ω₈** (the L2 keystone).

---

## 7. Status

v0.1 foundation. Python reference + 14 passing adversarial tests (incl. Ω₈). Next: flesh out `cm.*`
payload schemas from the ΣBUS-CM spec, the maritime membrane adapter, and wire the Python protocol to the
Autopoiesis-hosted Rust transport runtime.

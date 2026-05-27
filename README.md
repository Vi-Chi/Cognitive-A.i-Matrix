# ΣBUS — Sigma Bus

> *The sum of all streams.*

**ΣBUS** is a lightweight, open, transport-agnostic protocol for identity, discovery, and structured communication between autonomous AI agents in physical systems.

---

## What problem does this solve?

Existing standards cover instruments (NMEA), autopilots (MAVLink), and data (Signal K). Nobody has defined how **autonomous AI agents** identify themselves, discover peers, exchange world-model state, negotiate conflicting actions, or delegate control authority.

ΣBUS fills that gap. It is the agent-layer protocol — sitting above OSI Layer 7 — specifically designed for autonomous reasoning systems in safety-critical, resource-constrained, and intermittently-connected environments.

---

## Design Goals

- **Lightweight** — minimal implementation fits a microcontroller
- **Transport-agnostic** — NATS, MQTT, ZeroMQ, or serial
- **Offline-capable** — designed for intermittent connectivity
- **Trust-explicit** — every message carries trust metadata, trust decays
- **Provenance-mandatory** — every piece of data carries its origin chain
- **Safety-first** — human authority is inalienable at every protocol level

---

## Repository Structure

```
sigmabus/
|-- SIGMABUS-CM-SPEC.md          Main specification (start here)
|-- SIGMABUS-LLM.md              LLM agent extension
|-- sigma-bus-cognitive-matrix-v0.1.md
|-- schemas/
|   |-- aid.schema.json          Agent Identity Descriptor JSON Schema
|   `-- cm-message.schema.json   CM Message JSON Schema
|-- examples/
|   `-- 02-collision-avoidance.md
|-- sigma-bus-rust/
|   |-- src/lib.rs              Rust v1 envelope types and signing helpers
|   `-- examples/
|-- src/
|   |-- sigmabus_core.py         Minimal reference helpers
|   `-- run_simulation.py        Local negotiation trace smoke simulation
`-- config/
    `-- nats-edge.conf           Example local NATS JetStream edge config
```

---

## Quick Concepts

### Agent Identity Descriptor (AID)

Every agent has a signed identity document declaring what it can perceive, what it can control, and how fast it reasons. Like a passport — verifiable, versioned, broadcast on join.

### Semantic Envelope

Every message and data item carries provenance, trust score, timestamps (origin, received, expiry), derivation chain, and access control. Not decoration — load-bearing structure.

### CM Message Types

| Category | Types |
|---|---|
| Lifecycle | ANNOUNCE, WITHDRAW, HEARTBEAT |
| Information | QUERY, INFORM |
| Action | REQUEST, CONFIRM, FAIL |
| Negotiation | PROPOSE, AGREE, REFUSE, RETRACT |
| Control | DELEGATE, RESUME |
| Alert | ALERT |

### Trust Model

Trust is initialised by class (sovereign/federated/claimed/anonymous), modified by observed behaviour, and decays over time. An agent's messages with effective trust < 0.1 are discarded. Trust is persisted across sessions — reputation is earned, not assumed.

### Negotiation

Agents negotiate planned actions using PROPOSE / AGREE / REFUSE before execution. Every proposal has a TTL and a fallback action — if no agreement is reached, the agent executes a safe autonomous fallback, not nothing.

---

## Conformance Levels

| Level | Description |
|---|---|
| 1 — Minimal | ANNOUNCE, HEARTBEAT, QUERY/INFORM, discovery, signing |
| 2 — Standard | + REQUEST/ACTION, PROPOSE/NEGOTIATE, ALERT, trust tracking |
| 3 — Gateway | + DELEGATE/RESUME, cross-platform federation, link-adaptive transport |

---

## Primary Use Cases

- **Autonomous maritime vessels** — multiple agents (navigation, collision avoidance, engine, communications) coordinating across a vessel, and between vessels
- **Vessel-to-vessel coordination** — COLREGs-compliant crossing negotiation without human intervention
- **Port traffic management** — vessel agent registers intent, port agent allocates berth and approach
- **Multi-platform SIGINT** — sensor platforms register coverage, report detections with provenance, cooperatively task collection
- **Industrial automation** — agents coordinate handoffs, availability, and maintenance windows

---

## Status

Working Draft v0.1. Not yet reviewed by any standards body. Breaking changes possible before v1.0.

Contributions, feedback, and implementations welcome.

---

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).

---

## Origin

Developed from first principles during the design of an autonomous sailing vessel (Wibo 835 steel sloop) targeting offshore and circumnavigation capability. The protocol emerged from the practical need to coordinate multiple AI agents across navigation, propulsion, power, and communications domains under intermittent satellite connectivity, with no central coordination infrastructure and strict safety requirements.

The maritime context is the primary design driver. The protocol is domain-agnostic.

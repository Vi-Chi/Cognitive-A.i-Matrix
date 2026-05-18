# ΣBUS Communication Module (CM)
## Specification — Draft v0.1

**Status:** Working Draft  
**Date:** 2025-05-18  
**Authors:** Wibo835 Autonomous Vessel Project  
**License:** GPL-3.0-only  
**Repository:** https://github.com/Vi-Chi/sigmabus  

---

> **ΣBUS** (Sigma Bus) — *the sum of all streams*  
> A lightweight, open, transport-agnostic protocol for identity, discovery,  
> and structured communication between autonomous AI agents.

---

## Abstract

Existing communication standards address instruments (NMEA), autopilots (MAVLink), and data (Signal K), but no standard defines how autonomous AI agents identify themselves, discover peers, exchange world-model state, or negotiate actions in a distributed autonomous system. ΣBUS CM defines that layer. It is designed for edge deployment on resource-constrained hardware, operation under intermittent connectivity, and safety-critical environments where trust, provenance, and auditability are non-negotiable. The protocol is transport-agnostic, operating over NATS JetStream, MQTT, ZeroMQ, or serial links with equal correctness.

---

## Status of This Document

This document is a working draft. It has not been reviewed by any standards body. Implementors are encouraged to experiment and provide feedback. Breaking changes may occur before v1.0. Stability is not guaranteed between minor versions in the 0.x series.

The key words MUST, MUST NOT, REQUIRED, SHALL, SHOULD, SHOULD NOT, RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in RFC 2119.

---

## Table of Contents

1. [Introduction](#1-introduction)  
2. [Terminology](#2-terminology)  
3. [Architecture Overview](#3-architecture-overview)  
4. [Naming and Addressing](#4-naming-and-addressing)  
5. [Agent Identity Descriptor (AID)](#5-agent-identity-descriptor-aid)  
6. [Semantic Envelope](#6-semantic-envelope)  
7. [CM Message Types](#7-cm-message-types)  
8. [Conversation Model](#8-conversation-model)  
9. [Trust Model](#9-trust-model)  
10. [Discovery Protocol](#10-discovery-protocol)  
11. [Negotiation Protocol](#11-negotiation-protocol)  
12. [Control Delegation](#12-control-delegation)  
13. [Transport Bindings](#13-transport-bindings)  
14. [Security](#14-security)  
15. [Conformance](#15-conformance)  
16. [Relation to Existing Standards](#16-relation-to-existing-standards)  
17. [Design Rationale](#17-design-rationale)  

Appendix A — Message Schemas (JSON Schema)  
Appendix B — Example Conversations  
Appendix C — Glossary  
Appendix D — Change Log  

---

## 1. Introduction

### 1.1 Motivation

The deployment of autonomous AI agents across physical systems is accelerating. Vessels, vehicles, and installations increasingly run multiple concurrent AI agents — each with a domain of perception, reasoning, and control. These agents must coordinate: they share sensors, they have overlapping authority, and their decisions have physical consequences.

No existing standard addresses how these agents should:

- Establish verifiable identity
- Advertise capability and authority boundaries
- Exchange world-model state with provenance metadata
- Negotiate conflicting planned actions
- Delegate and resume control authority
- Operate safely under partial connectivity

ΣBUS CM fills this gap. It defines the agent-layer protocol — the stratum above OSI Layer 7 and above application data formats — specifically for autonomous reasoning agents in physical systems.

### 1.2 Design Principles

**P1 — Lightweight by default.** The minimal conformant implementation fits on a microcontroller. Core message types are expressible in under 500 bytes.

**P2 — Transport-agnostic.** The protocol makes no assumption about the underlying transport. Correct operation is achievable over TCP/IP, MQTT, ZeroMQ, serial, or satellite links with differing reliability and bandwidth characteristics.

**P3 — Offline-capable.** An agent MUST be able to operate in degraded mode with no peer connectivity. Reconnection and state reconciliation are first-class protocol concerns.

**P4 — Trust is explicit and decaying.** Every message carries trust metadata. Trust is not binary and is not assumed. It is earned, tracked, and decays with time and adverse events.

**P5 — Provenance is mandatory.** The origin, derivation path, and temporal metadata of all exchanged data MUST be preserved across the system. It MUST always be possible to trace a decision back to its inputs.

**P6 — Safety over liveness.** When in doubt, agents MUST default to safe inaction rather than autonomous action. A message that cannot be validated MUST be discarded, not acted upon.

**P7 — Human authority is inalienable.** No agent-to-agent negotiation can override a direct human command. Human authority MUST be expressible at every layer of the protocol.

### 1.3 Scope

ΣBUS CM specifies:
- Agent identity structure and verification
- The semantic envelope attached to all messages
- The vocabulary of CM message types and their required fields
- Conversation threading and state machine semantics
- Trust classes, modifiers, and reputation tracking
- Discovery over local and federated networks
- Negotiation and control delegation procedures
- Transport bindings for NATS, MQTT, and ZeroMQ

ΣBUS CM does not specify:
- Application-layer data formats (defer to Signal K, NMEA, MAVLink)
- Internal agent reasoning or planning algorithms
- Specific sensor interfaces
- UI or human interaction protocols

### 1.4 Use Cases

**UC1 — Maritime autonomous vessel.** Multiple AI agents (navigation, collision avoidance, engine management, communications) running on a single-vessel computing platform, coordinating autonomously with intermittent satellite connectivity.

**UC2 — Vessel-to-vessel coordination.** Two autonomous vessels approaching each other negotiate a COLREGs-compliant crossing arrangement without human intervention, communicating over VHF digital link.

**UC3 — Port traffic integration.** An autonomous vessel registers its intent with a port traffic management agent running ashore, receives berth assignment and approach instructions.

**UC4 — Multi-platform SIGINT.** Multiple sensor platforms (airborne, maritime, shore-based) register their coverage zones, report detections with provenance metadata, and cooperatively task collection resources.

**UC5 — Industrial automation.** Factory agents coordinate handoffs of physical work items, advertise machine availability, and negotiate maintenance windows without central coordination.

---

## 2. Terminology

**Agent** — An autonomous software process capable of perceiving its environment, reasoning about it, and taking actions. In the context of this specification, agents are assumed to contain or interface with a language model or equivalent reasoning system.

**AID** — Agent Identity Descriptor. The structured document that defines an agent's identity, capabilities, and operating parameters.

**CM** — Communication Module. This specification and the protocol it defines.

**Conversation** — A bounded, threaded exchange of CM Messages between two or more agents, having a defined type, state machine, and completion condition.

**Platform** — The physical or virtual host on which agents run. A vessel, vehicle, installation, or server. A platform may host multiple agents.

**Path** — A hierarchical dot-separated address for a data stream. See Section 4.

**Semantic Envelope** — The metadata wrapper attached to every message and data item in a ΣBUS system, carrying provenance, trust, temporal, and access control information.

**Trust Class** — A categorical trust level assigned to an agent based on identity verification and relationship.

**World Model** — An agent's internal representation of the state of its environment, derived from its perception of data streams.

**Gateway** — A specialised ΣBUS node that bridges two ΣBUS networks (e.g., two vessels) with different connectivity characteristics.

**Proposal** — A CM Message of type PROPOSE that offers a coordinated action for negotiation between agents.

**Sovereign Agent** — An agent that is native to a platform, signed by the platform's Certificate Authority, and granted full operational trust on that platform.

---

## 3. Architecture Overview

### 3.1 Layer Model

ΣBUS CM occupies a defined position in the communication stack:

```
┌────────────────────────────────────────────────────────┐
│  L9  Negotiation Layer                                 │
│      Agent-to-agent intent, proposals, coordination    │
├────────────────────────────────────────────────────────┤
│  L8  ΣBUS CM  (this specification)                     │
│      Identity, trust, conversation, delegation         │
├────────────────────────────────────────────────────────┤
│  L8  Semantic Envelope                                 │
│      Provenance, trust score, temporal metadata, ACL   │
├────────────────────────────────────────────────────────┤
│  L7  Application                                       │
│      Signal K, NMEA, MAVLink, custom schemas           │
├────────────────────────────────────────────────────────┤
│  L4-6 Transport / Session / Presentation               │
│  L1-3 Physical / Data Link / Network                   │
└────────────────────────────────────────────────────────┘
```

### 3.2 System Components

A ΣBUS deployment consists of:

```
Platform
├── Matrix Registry        — schema library, path registry, health tracking
├── Matrix Bus (ΣBUS)      — message routing, validation, windowing, CEP
├── Agent Interface        — filtered world-model view for each agent
├── Agents (N)
│   ├── Sovereign agents   — platform-native, full trust
│   └── Federated agents   — external, limited trust
└── Gateway (optional)     — bridges to peer platforms
```

### 3.3 Data Flow

```
[Physical world]
     │ sensors, RF, serial, CAN
     ▼
[Ingestors]
     │ parse, validate, wrap in Semantic Envelope
     ▼
[Matrix Bus]
     │ schema validate, trust gate, route, window
     │ CEP pattern matching
     ▼
[Agent Interface]       ← filtered, prioritised, rate-limited
     │
     ▼
[Agent]                 ← reasons, produces CM Messages
     │
     ▼
[Matrix Bus]            ← commands flow back into bus
     │
     ▼
[Actuators / other agents / gateway]
```

---

## 4. Naming and Addressing

### 4.1 Path Structure

All data streams and agents are addressed by a hierarchical path:

```
{platform_id}.{domain}.{subdomain}.{entity}.{attribute}
```

Examples:

```
wibo835.nav.position.gps_primary.lat
wibo835.nav.ais.target_123456789.cpa_nm
wibo835.engine.port.coolant_temp_c
wibo835.power.bank_a.soc_pct
wibo835.agent.nav_agent.state
wibo835.meta.bus.health
wibo835.meta.alert.cpa_critical
mv_osprey.nav.position.ais.lat          ← external platform data
meta.federation.peers                   ← federation-level
```

### 4.2 Reserved Domains

| Domain | Purpose |
|---|---|
| `nav` | Navigation data: position, motion, routing, AIS |
| `engine` | Propulsion: RPM, temperatures, fuel, hours |
| `power` | Electrical: batteries, solar, wind, load |
| `comms` | Communications: HF, VHF, satellite, AIS TX |
| `safety` | Alarms, bilge, fire, flooding, MOB |
| `environment` | Wind, weather, barometer, sea state |
| `agent` | Agent state, decisions, commands |
| `meta` | System self-description, bus health, alerts |
| `cmd` | Command paths — agent-writable control targets |

### 4.3 Reserved Prefixes

| Prefix | Meaning |
|---|---|
| `meta.alert.*` | CEP-generated alerts, always priority 1 |
| `meta.federation.*` | Gateway and peer registration |
| `agent.{uid}.*` | Agent-generated data, flagged as inferred |
| `cmd.*` | Command paths — restricted write access |

### 4.4 Agent Addressing in CM

CM messages use a separate addressing scheme from data paths:

```
cm.{platform_id}.broadcast               ← all agents on platform
cm.{platform_id}.{agent_uid}             ← directed to specific agent
cm.{platform_id}.role.{role}             ← all agents of a role
cm.federation.{platform_id}              ← cross-platform
```

### 4.5 Naming Rules

1. All components MUST be lowercase ASCII, digits, or underscores.
2. Dots are used exclusively as hierarchy separators.
3. Paths MUST be fully qualified — no relative paths.
4. The `meta.*` and `cmd.*` domains are reserved. User-defined data MUST NOT use them.
5. A platform MUST use a consistent, unique `platform_id` across all sessions.
6. Paths ending in `.*` are wildcard subscriptions, valid only in subscribe operations.

---

## 5. Agent Identity Descriptor (AID)

### 5.1 Overview

The AID is the agent's verifiable identity document. Every conformant agent MUST have an AID. The AID is signed by the platform Certificate Authority on sovereign agents, or self-signed on uncertified agents. It is broadcast on agent startup and stored by all peers.

### 5.2 AID Structure

```json
{
  "aid_version": "1.0",

  "identity": {
    "uid": "agt-wibo835-nav-001",
    "platform_id": "wibo835",
    "role": "navigation",
    "tier": 2,
    "display_name": "Navigation Agent",
    "description": "COLREGs-aware route planning and collision avoidance"
  },

  "provenance": {
    "created_at": "2025-05-01T12:00:00Z",
    "software_version": "1.2.0",
    "model_id": "qwen2-vl-2b-instruct",
    "model_quantization": "int8",
    "runtime": "llama.cpp",
    "hardware": "rpi5-hailo10h"
  },

  "capabilities": {
    "perceives": [
      "wibo835.nav.*",
      "wibo835.environment.*",
      "wibo835.meta.alert.*"
    ],
    "controls": [
      "wibo835.cmd.autopilot.heading",
      "wibo835.cmd.waypoint.active"
    ],
    "reasoning_domains": [
      "colregs",
      "route_planning",
      "collision_avoidance",
      "weather_routing"
    ],
    "cm_message_types": [
      "ANNOUNCE", "WITHDRAW", "HEARTBEAT",
      "QUERY", "INFORM",
      "PROPOSE", "AGREE", "REFUSE", "RETRACT",
      "ALERT", "DELEGATE"
    ]
  },

  "performance": {
    "latency_p50_ms": 450,
    "latency_p99_ms": 1200,
    "update_rate_hz": 1.0,
    "max_context_tokens": 4096,
    "offline_capable": true,
    "degraded_mode": "rule_engine_fallback"
  },

  "trust": {
    "trust_class": "sovereign",
    "pubkey_algorithm": "ed25519",
    "pubkey": "base64:abc123...",
    "cert_issuer": "wibo835-vessel-ca",
    "cert_expires": "2026-05-01T00:00:00Z"
  },

  "operational": {
    "authority_scope": [
      "wibo835.cmd.autopilot.*",
      "wibo835.cmd.waypoint.*"
    ],
    "human_override_path": "wibo835.cmd.helm.human_active",
    "emergency_stop_path": "wibo835.cmd.autopilot.emergency_stop",
    "max_rudder_deg": 15,
    "requires_confirmation_above_priority": 3
  },

  "signature": "base64:sig..."
}
```

### 5.3 Field Definitions

#### 5.3.1 identity

| Field | Required | Description |
|---|---|---|
| `uid` | REQUIRED | Globally unique agent identifier. MUST be stable across restarts. Format: `agt-{platform_id}-{role}-{sequence}` |
| `platform_id` | REQUIRED | The platform this agent is native to |
| `role` | REQUIRED | Functional role. Values: `navigation`, `engine`, `safety`, `communications`, `power`, `weather`, `command`, `gateway`, `observer` |
| `tier` | REQUIRED | Reasoning tier: 1=rule/local model (<100ms), 2=small LLM (~500ms), 3=large LLM (1-5s) |
| `display_name` | OPTIONAL | Human-readable name |
| `description` | OPTIONAL | One-line description |

#### 5.3.2 provenance

| Field | Required | Description |
|---|---|---|
| `created_at` | REQUIRED | ISO 8601 timestamp of AID creation |
| `software_version` | REQUIRED | SemVer of agent software |
| `model_id` | OPTIONAL | Underlying LLM model identifier |
| `model_quantization` | OPTIONAL | Quantization applied |
| `runtime` | OPTIONAL | Inference runtime |
| `hardware` | OPTIONAL | Hardware descriptor |

#### 5.3.3 capabilities

| Field | Required | Description |
|---|---|---|
| `perceives` | REQUIRED | List of path patterns the agent subscribes to. Wildcards permitted. |
| `controls` | REQUIRED | List of exact paths the agent is authorised to write. No wildcards. |
| `reasoning_domains` | REQUIRED | List of knowledge domains the agent can reason about |
| `cm_message_types` | REQUIRED | List of CM message types this agent supports |

#### 5.3.4 performance

| Field | Required | Description |
|---|---|---|
| `latency_p50_ms` | RECOMMENDED | Median response latency |
| `latency_p99_ms` | RECOMMENDED | 99th percentile response latency |
| `update_rate_hz` | REQUIRED | Maximum rate at which this agent produces outputs |
| `offline_capable` | REQUIRED | Boolean — can this agent function without connectivity? |
| `degraded_mode` | OPTIONAL | Description of behaviour under degraded connectivity |

#### 5.3.5 trust

| Field | Required | Description |
|---|---|---|
| `trust_class` | REQUIRED | See Section 9.2 |
| `pubkey_algorithm` | REQUIRED | Signature algorithm. MUST be `ed25519` |
| `pubkey` | REQUIRED | Base64-encoded public key |
| `cert_issuer` | CONDITIONAL | REQUIRED for `sovereign` and `federated` trust classes |
| `cert_expires` | CONDITIONAL | REQUIRED if cert_issuer is present |

#### 5.3.6 operational

| Field | Required | Description |
|---|---|---|
| `authority_scope` | REQUIRED | Exact list of command paths this agent may actuate |
| `human_override_path` | REQUIRED | Path that, when true, suspends this agent's actuation authority |
| `emergency_stop_path` | REQUIRED | Path that triggers immediate safe-state halt |
| `requires_confirmation_above_priority` | OPTIONAL | Actions above this priority level require explicit confirmation |

### 5.4 AID Versioning

An AID MAY be updated during operation (e.g., capability expansion). When updated:
- The `software_version` MUST be incremented
- A new `ANNOUNCE` message MUST be broadcast
- Peers MUST replace their stored AID for this uid
- The `uid` MUST NOT change

### 5.5 AID Signing

The AID is signed using ed25519. The signature field covers all fields except `signature` itself, serialised as canonical JSON (sorted keys, no whitespace).

Self-signed AIDs (trust_class `claimed` or `anonymous`) are valid but MUST be treated with correspondingly reduced trust per Section 9.

---

## 6. Semantic Envelope

Every message and data item in a ΣBUS system MUST be wrapped in a Semantic Envelope. The envelope is not optional. It is the metadata layer that makes trust, provenance, and auditability tractable.

### 6.1 Envelope Structure

```json
{
  "env_version": "1.0",

  "identity": {
    "msg_id": "01HV7Q2KPNZ8X...",
    "path": "wibo835.nav.position.gps_primary.lat",
    "schema_id": "position.fix",
    "schema_version": 3
  },

  "temporal": {
    "t_origin_us": 1716123456891234,
    "t_received_us": 1716123456983421,
    "t_expires_us": 1716123458891234,
    "latency_us": 92187
  },

  "provenance": {
    "source_id": "gps_primary_antenna",
    "source_type": "sensor",
    "interface": "serial_nmea",
    "path_history": ["antenna", "nmea_mux_port2", "signalk_plugin"],
    "derived_from": [],
    "derivation_fn": null
  },

  "trust": {
    "trust_score": 0.97,
    "trust_class": "hardware",
    "cross_validated": true,
    "validators": ["gps_secondary", "imu_position_estimate"],
    "anomaly_score": 0.02
  },

  "access": {
    "consumers": ["*"],
    "producer_uid": "agt-wibo835-sensor-001",
    "write_authorised": true
  },

  "retention": {
    "class": "voyage",
    "archive_priority": 3,
    "compress": false
  },

  "operational": {
    "priority": 5,
    "data_class": "sensor",
    "classification": "routine"
  },

  "signature": "base64:sig...",

  "payload": 52.3701,

  "annotations": {}
}
```

### 6.2 Temporal Fields

All timestamps are Unix microseconds (integer). This precision is required for TDOA calculations and event ordering in distributed systems.

| Field | Required | Description |
|---|---|---|
| `t_origin_us` | REQUIRED | When the physical event occurred |
| `t_received_us` | REQUIRED | When this node received/created the message |
| `t_expires_us` | OPTIONAL | After this time, the value is stale and MUST NOT be acted upon |
| `latency_us` | OPTIONAL | `t_received_us - t_origin_us` |

### 6.3 Trust Fields

| Field | Range | Description |
|---|---|---|
| `trust_score` | 0.0 – 1.0 | Current trust. Subject to decay and modification |
| `trust_class` | enum | Base trust class of the source. See Section 9 |
| `cross_validated` | bool | True if independently confirmed by another source |
| `validators` | list | Source IDs that confirmed this value |
| `anomaly_score` | 0.0 – 1.0 | 0=expected, 1=extreme anomaly |

### 6.4 Effective Trust Calculation

The effective trust of a message at time T is:

```
effective_trust(T) = clamp(
    base_trust
    - age_decay(T - t_origin_us)
    - (anomaly_score × 0.5)
    + (0.1 if cross_validated else 0),
    0.0, 1.0
)
```

Age decay is data-type dependent. Reference values:

| Data type | Half-life |
|---|---|
| GPS position | 2 seconds |
| AIS target state | 3 minutes |
| Engine telemetry | 5 seconds |
| Weather forecast | 6 hours |
| Chart data | indefinite |
| Agent decision | 30 seconds |

Messages with `effective_trust < 0.1` MUST be discarded and MUST NOT be acted upon.

### 6.5 Annotations

The `annotations` field is a key-value store for agent-generated shadow data. Agents MAY write annotations without modifying the payload. Annotations persist with the envelope through the bus.

```json
"annotations": {
  "nav_agent_confidence": {"value": 0.94, "t": 1716123456},
  "cross_check_delta_kn": {"value": 0.1, "t": 1716123456},
  "flagged_for_review": {"value": false, "t": 1716123456}
}
```

Annotation keys MUST be prefixed with the writing agent's role to avoid collision: `{role}_{key}`.

---

## 7. CM Message Types

### 7.1 Overview

CM Messages are a distinct message class, separate from data stream messages. They flow on the `cm.*` subject space. Every CM Message is itself wrapped in a Semantic Envelope with `data_class: "cm"`.

### 7.2 Lifecycle Messages

#### ANNOUNCE

Sent by an agent on startup and when its AID changes. MUST be sent before any other message type.

```json
{
  "msg_type": "ANNOUNCE",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-nav-001",
  "timestamp_us": 1716123456000000,
  "aid": { /* full AID document */ },
  "reason": "startup"
}
```

`reason` values: `startup`, `aid_update`, `reconnect`, `request`

On receiving ANNOUNCE, peers MUST:
1. Store or replace the AID for this uid
2. Update their peer trust registry
3. If this is a new peer, optionally send their own ANNOUNCE in return

#### WITHDRAW

Sent by an agent before clean shutdown.

```json
{
  "msg_type": "WITHDRAW",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-nav-001",
  "timestamp_us": 1716123456000000,
  "reason": "shutdown",
  "handover_uid": "agt-wibo835-pilot-001"
}
```

`reason` values: `shutdown`, `maintenance`, `fault`, `upgrade`  
`handover_uid`: OPTIONAL — uid of agent receiving delegated authority

On receiving WITHDRAW, peers MUST:
1. Mark this agent as absent in their registry
2. If this agent held delegated authority, process handover or escalate

#### HEARTBEAT

Sent periodically by every active agent. Default interval: 10 seconds. MUST be sent at least every 30 seconds.

```json
{
  "msg_type": "HEARTBEAT",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-nav-001",
  "timestamp_us": 1716123456000000,
  "sequence": 1842,
  "status": "nominal",
  "load": 0.43,
  "world_model_hash": "sha256:a3f9...",
  "active_conversations": 2,
  "alerts_pending": 0
}
```

`status` values: `nominal`, `degraded`, `offline_mode`, `fault`

Absence of HEARTBEAT for 3× the declared interval MUST cause peers to mark this agent as `absent`.

### 7.3 Information Messages

#### QUERY

Request for current state information from a peer.

```json
{
  "msg_type": "QUERY",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-nav-001",
  "receiver_uid": "agt-wibo835-engine-001",
  "timestamp_us": 1716123456000000,
  "conversation_id": "conv-uuid",
  "subject": "engine_available_power",
  "query": {
    "paths": ["wibo835.engine.port.rpm", "wibo835.engine.port.temp_coolant"],
    "include_history_s": 60,
    "min_trust": 0.7
  },
  "response_required_by_us": 1716123461000000
}
```

`response_required_by_us`: deadline for response. If not met, sender may assume agent is unavailable.

#### INFORM

Response to a QUERY, or unsolicited state broadcast.

```json
{
  "msg_type": "INFORM",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-engine-001",
  "receiver_uid": "agt-wibo835-nav-001",
  "timestamp_us": 1716123457200000,
  "conversation_id": "conv-uuid",
  "reply_to": "query-msg-uuid",
  "subject": "engine_available_power",
  "content": {
    "wibo835.engine.port.rpm": {
      "value": 1850,
      "trust": 0.96,
      "age_ms": 120
    },
    "wibo835.engine.port.temp_coolant": {
      "value": 78.4,
      "trust": 0.96,
      "age_ms": 120
    },
    "assessment": "Engine nominal. Sustained max RPM available."
  }
}
```

### 7.4 Action Messages

#### REQUEST

Asks a peer to execute a specific action.

```json
{
  "msg_type": "REQUEST",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-nav-001",
  "receiver_uid": "agt-wibo835-pilot-001",
  "timestamp_us": 1716123456000000,
  "conversation_id": "conv-uuid",
  "priority": 3,
  "subject": "alter_course",
  "action": {
    "type": "set_heading",
    "value": 285,
    "unit": "degrees_true",
    "duration_s": 300,
    "reason": "Traffic separation scheme entry",
    "colreg_rule": null
  },
  "constraints": {
    "max_rate_of_turn_dpm": 5,
    "revert_to_previous_on_complete": false
  },
  "expires_us": 1716123516000000
}
```

`priority`: 1=emergency, 2=urgent, 3=elevated, 4=normal, 5–10=background

#### CONFIRM

Successful execution of a REQUEST.

```json
{
  "msg_type": "CONFIRM",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-pilot-001",
  "receiver_uid": "agt-wibo835-nav-001",
  "timestamp_us": 1716123456900000,
  "conversation_id": "conv-uuid",
  "reply_to": "request-msg-uuid",
  "subject": "alter_course",
  "result": {
    "executed": true,
    "new_heading": 285,
    "execution_time_us": 1716123456850000,
    "notes": "Course alteration initiated. ETA to new heading: 45s at current ROT."
  }
}
```

#### FAIL

Failed execution of a REQUEST.

```json
{
  "msg_type": "FAIL",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-pilot-001",
  "receiver_uid": "agt-wibo835-nav-001",
  "timestamp_us": 1716123456900000,
  "conversation_id": "conv-uuid",
  "reply_to": "request-msg-uuid",
  "subject": "alter_course",
  "failure": {
    "code": "AUTHORITY_SUSPENDED",
    "reason": "Human helm override active",
    "recoverable": true,
    "retry_after_s": null
  }
}
```

Failure codes: `AUTHORITY_SUSPENDED`, `CAPABILITY_UNAVAILABLE`, `CONSTRAINT_VIOLATED`, `RESOURCE_CONFLICT`, `TRUST_INSUFFICIENT`, `TIMEOUT`, `INTERNAL_ERROR`

### 7.5 Negotiation Messages

See Section 11 for full negotiation protocol.

#### PROPOSE

Offers a coordinated action for peer review and agreement.

```json
{
  "msg_type": "PROPOSE",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-nav-001",
  "receiver_uid": "agt-mv-osprey-nav-001",
  "timestamp_us": 1716123456000000,
  "conversation_id": "conv-uuid",
  "priority": 2,
  "proposal_id": "prop-collision-001",
  "proposal_ttl_s": 30,
  "subject": "collision_avoidance_manoeuvre",
  "situation": {
    "cpa_nm": 0.28,
    "tcpa_min": 8.2,
    "bearing_deg": 047,
    "geometry": "crossing_give_way"
  },
  "proposed_actions": [
    {
      "agent_uid": "agt-wibo835-nav-001",
      "action": "alter_course_starboard",
      "value": 30,
      "unit": "degrees_relative",
      "colreg_rule": 16,
      "rationale": "Give-way vessel, Rule 16 applies"
    }
  ],
  "requested_actions": [
    {
      "agent_uid": "agt-mv-osprey-nav-001",
      "action": "maintain_course_and_speed",
      "colreg_rule": 17,
      "rationale": "Stand-on vessel, Rule 17 duty to maintain"
    }
  ],
  "fallback": {
    "if_no_agreement_by_us": 1716123471000000,
    "autonomous_action": "reduce_speed_to_3kn_and_alert_crew"
  }
}
```

#### AGREE

Acceptance of a PROPOSE.

```json
{
  "msg_type": "AGREE",
  "msg_id": "uuid",
  "sender_uid": "agt-mv-osprey-nav-001",
  "receiver_uid": "agt-wibo835-nav-001",
  "timestamp_us": 1716123460000000,
  "conversation_id": "conv-uuid",
  "reply_to": "propose-msg-uuid",
  "proposal_id": "prop-collision-001",
  "commitment": {
    "action": "maintain_course_and_speed",
    "until_us": 1716124000000000,
    "monitoring_path": "mv-osprey.nav.position.ais.cog_deg"
  }
}
```

#### REFUSE

Rejection of a PROPOSE, with optional counter-proposal.

```json
{
  "msg_type": "REFUSE",
  "msg_id": "uuid",
  "sender_uid": "agt-mv-osprey-nav-001",
  "receiver_uid": "agt-wibo835-nav-001",
  "timestamp_us": 1716123460000000,
  "conversation_id": "conv-uuid",
  "reply_to": "propose-msg-uuid",
  "proposal_id": "prop-collision-001",
  "refusal": {
    "code": "CONSTRAINT_VIOLATED",
    "reason": "Shallow water 0.3nm to starboard prevents starboard alteration",
    "counter_proposal_id": "prop-collision-002"
  }
}
```

#### RETRACT

Withdraws a previous PROPOSE before agreement.

```json
{
  "msg_type": "RETRACT",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-nav-001",
  "receiver_uid": "agt-mv-osprey-nav-001",
  "timestamp_us": 1716123465000000,
  "conversation_id": "conv-uuid",
  "reply_to": "propose-msg-uuid",
  "proposal_id": "prop-collision-001",
  "reason": "Situation resolved — CPA now 1.2nm on current courses"
}
```

### 7.6 Control Messages

#### DELEGATE

Transfers authority over a set of control paths to another agent.

```json
{
  "msg_type": "DELEGATE",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-nav-001",
  "receiver_uid": "agt-wibo835-pilot-001",
  "timestamp_us": 1716123456000000,
  "conversation_id": "conv-uuid",
  "delegation_id": "del-001",
  "scope": {
    "paths": ["wibo835.cmd.autopilot.*"],
    "duration_s": 3600,
    "revocable": true
  },
  "constraints": {
    "max_heading_change_deg": 45,
    "max_speed_kn": 8,
    "min_speed_kn": 2,
    "no_go_zones": ["zone-shallow-north"]
  },
  "handback_trigger": {
    "paths": ["wibo835.safety.alarm.*"],
    "condition": "any_active"
  }
}
```

#### RESUME

Reclaims previously delegated authority.

```json
{
  "msg_type": "RESUME",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-nav-001",
  "receiver_uid": "agt-wibo835-pilot-001",
  "timestamp_us": 1716126456000000,
  "conversation_id": "conv-uuid",
  "delegation_id": "del-001",
  "reason": "Approaching waypoint — resuming direct navigation control"
}
```

### 7.7 Alert Messages

#### ALERT

Broadcasts a detected condition to all subscribed agents. ALERT is the only message type that is always broadcast, never directed.

```json
{
  "msg_type": "ALERT",
  "msg_id": "uuid",
  "sender_uid": "agt-wibo835-nav-001",
  "receiver_uid": null,
  "timestamp_us": 1716123456000000,
  "priority": 1,
  "alert_id": "alert-cpa-001",
  "category": "collision_risk",
  "severity": "urgent",
  "subject": "CPA below threshold",
  "data": {
    "target_mmsi": 123456789,
    "target_name": "MV OSPREY",
    "cpa_nm": 0.28,
    "tcpa_min": 8.2,
    "recommended_action": "PROPOSE collision avoidance to target"
  },
  "expires_us": 1716124056000000,
  "source_pattern": "cpa_critical",
  "evidence_paths": [
    "wibo835.nav.ais.target_123456789.cpa_nm",
    "wibo835.nav.ais.target_123456789.tcpa_min"
  ]
}
```

`category` values: `collision_risk`, `grounding_risk`, `equipment_fault`, `power_critical`, `communications_loss`, `weather_severe`, `man_overboard`, `fire`, `flooding`

`severity` values: `emergency`, `urgent`, `elevated`, `advisory`

---

## 8. Conversation Model

### 8.1 Threading

Every exchange between agents MUST be associated with a `conversation_id`. Conversations are the unit of state for the CM layer — they have a type, a state machine, and a completion condition.

A `conversation_id` is a UUID generated by the conversation initiator. All messages in the conversation reference this ID. Implementations MUST store conversation state and MUST handle out-of-order message delivery.

### 8.2 Conversation Types

| Type | Initiating Message | Terminal States |
|---|---|---|
| `LIFECYCLE` | ANNOUNCE / WITHDRAW | implicit on WITHDRAW |
| `QUERY_INFORM` | QUERY | INFORM received, or timeout |
| `REQUEST_ACTION` | REQUEST | CONFIRM or FAIL received |
| `NEGOTIATION` | PROPOSE | AGREE, REFUSE, RETRACT, or timeout |
| `DELEGATION` | DELEGATE | RESUME, or delegation duration expires |
| `ALERT_RESPONSE` | ALERT | no terminal state — fire and forget |

### 8.3 State Machines

#### QUERY_INFORM

```
[INIT]
  initiator sends QUERY
  → [PENDING]
    responder sends INFORM
    → [COMPLETE]
    OR: timeout expires
    → [TIMED_OUT]
```

#### REQUEST_ACTION

```
[INIT]
  initiator sends REQUEST
  → [PENDING]
    responder sends CONFIRM
    → [COMPLETE]
    OR: responder sends FAIL
    → [FAILED]
    OR: expires_us reached
    → [EXPIRED]
```

#### NEGOTIATION

```
[INIT]
  initiator sends PROPOSE
  → [PROPOSED]
    peer sends AGREE
    → [AGREED]  ← both parties execute commitments
    OR: peer sends REFUSE (no counter)
    → [REFUSED]
    OR: peer sends REFUSE (with counter)
    → [COUNTER_PROPOSED]  ← re-enter negotiation on counter
    OR: initiator sends RETRACT
    → [RETRACTED]
    OR: proposal_ttl expires
    → [EXPIRED] ← initiator executes fallback action
```

#### DELEGATION

```
[INIT]
  delegator sends DELEGATE
  → [PENDING]
    delegatee sends CONFIRM
    → [ACTIVE]  ← delegatee holds authority
      delegator sends RESUME
      → [COMPLETED]
      OR: handback_trigger fires
      → [COMPLETED]
      OR: duration expires
      → [COMPLETED]
      OR: delegatee sends FAIL
      → [FAULTED] ← escalate to human
```

### 8.4 Timeout Handling

Every conversation type has a maximum duration. Implementations MUST enforce these:

| Conversation Type | Default Timeout |
|---|---|
| QUERY_INFORM | 5 seconds |
| REQUEST_ACTION | `expires_us` field, max 60s |
| NEGOTIATION | `proposal_ttl_s` field, max 120s |
| DELEGATION | `duration_s` field, max 24 hours |

On timeout, the initiating agent MUST log the timeout, update the peer trust record negatively, and execute the defined fallback action if one exists.

---

## 9. Trust Model

### 9.1 Overview

Trust in ΣBUS CM is not binary. Every agent maintains a trust score for every peer it has observed. Trust is initialised from the trust class, modified by observed behaviour, and decays over time. An agent MUST NOT act on a message whose effective trust falls below its configured minimum.

### 9.2 Trust Classes

| Class | Initial Score | Description |
|---|---|---|
| `sovereign` | 1.00 | Native agent, signed by platform CA. Full authority within declared scope. |
| `trusted_peer` | 0.85 | External agent with verified identity and established relationship. |
| `federated` | 0.70 | External system with valid certificate from a known CA. |
| `claimed` | 0.40 | Agent provides AID but no verifiable signing chain. |
| `anonymous` | 0.10 | No identity. Observe-only. |
| `blocked` | 0.00 | Explicitly blocked. All messages discarded. |

### 9.3 Trust Modifiers

Applied cumulatively to an agent's trust score based on observed behaviour:

| Event | Modifier |
|---|---|
| PROPOSE executed and outcome confirmed positive | +0.05 |
| INFORM content cross-validated as accurate | +0.02 |
| World model hash matches at verification | +0.01 per match |
| QUERY not answered within declared p99 latency | -0.05 |
| CONFIRM action led to negative outcome | -0.15 |
| INFORM content cross-validated as inaccurate | -0.20 |
| Message failed signature verification | -0.50 |
| Message violated declared capability scope | -0.30 |
| Repeated PROPOSE/REFUSE loop (>3 cycles, no resolution) | -0.10 |

Trust score is bounded [0.0, 1.0]. If score drops below 0.1, the agent MUST be flagged for review and all its messages treated as `anonymous` class until manually cleared.

### 9.4 Trust Decay

Trust decays in the absence of observed behaviour:

```
trust_at_t = initial_trust × e^(-λ × hours_since_last_positive_event)
```

Default decay constant λ = 0.02 (approximately 15% decay per day of inactivity).

Trust does NOT decay below `trust_class` floor while the agent is active and sending valid HEARTBEATs.

### 9.5 Trust Persistence

Trust scores MUST be persisted to non-volatile storage. Peer trust state MUST survive agent restarts. This enables long-term reputation building across voyages, sessions, and encounters.

### 9.6 Minimum Trust Thresholds

Implementations MUST enforce these defaults (configurable by platform operator):

| Action | Minimum Trust |
|---|---|
| Receive and log message | 0.05 |
| Update world model | 0.40 |
| Execute a REQUEST action | 0.70 |
| AGREE to a PROPOSAL | 0.75 |
| DELEGATE authority | 0.85 |
| Act on an ALERT without human confirmation | 0.80 |

---

## 10. Discovery Protocol

### 10.1 Local Discovery

On a local network, ΣBUS uses mDNS for zero-configuration discovery.

Service type: `_sigmabus._tcp.local`  
TXT record MUST contain: `aid_endpoint`, `platform_id`, `cm_version`

On startup, every agent MUST:
1. Register its mDNS service record
2. Browse for `_sigmabus._tcp.local` peers
3. Connect to each discovered peer's `aid_endpoint`
4. Send ANNOUNCE

On discovering a new peer, an agent SHOULD send its own ANNOUNCE to that peer.

### 10.2 Direct Bootstrap

Where mDNS is not available, agents MAY be configured with a static list of peer endpoints. Agents MUST attempt connection to all configured endpoints on startup.

### 10.3 Bus-Based Discovery

Where a shared message bus is available (NATS, MQTT), agents MUST:
1. Subscribe to `cm.{platform_id}.broadcast`
2. Send ANNOUNCE to `cm.{platform_id}.broadcast` on startup
3. Listen for ANNOUNCE from other agents
4. Build and maintain a local peer registry

### 10.4 Federated Discovery (Multi-Platform)

Each platform runs a Gateway agent responsible for federation.

```
Platform A (wibo835)               Platform B (mv_osprey)
  Gateway A                          Gateway B
    │                                   │
    │    ← bandwidth-constrained link → │
    │                                   │
  registers peer: mv_osprey          registers peer: wibo835
  subscribes: mv-osprey.nav.*       subscribes: wibo835.nav.*
```

Gateway-to-Gateway communication uses the same CM protocol but over a link-appropriate transport (satellite, VHF digital, LoRa, etc.) with message filtering:

**Cross-boundary message policy:**

| Message Type | Crosses boundary? |
|---|---|
| HEARTBEAT | Only if subscribed by peer |
| ANNOUNCE | Yes — always |
| ALERT (severity: emergency/urgent) | Yes — always |
| ALERT (severity: elevated/advisory) | Gateway-configured |
| PROPOSE / AGREE / REFUSE | Yes — always |
| QUERY / INFORM | Only if cross-platform query |
| DELEGATE | Only if cross-platform delegation |
| Raw data streams | Never by default — explicit subscription only |

Gateways MUST track link state (bandwidth, latency, reliability) and adapt message transmission accordingly. On a 600 baud HF link, only ALERT and PROPOSE cross; on a 100 Mbps fibre link, all message types may cross.

### 10.5 Peer Registry

Every agent MUST maintain a local peer registry:

```json
{
  "peer_registry": {
    "agt-wibo835-engine-001": {
      "aid": { /* stored AID */ },
      "trust_score": 0.94,
      "last_heartbeat_us": 1716123450000000,
      "status": "nominal",
      "active_conversations": ["conv-uuid-1"],
      "delegations_held": [],
      "first_seen_us": 1716000000000000,
      "positive_interactions": 847,
      "negative_interactions": 2
    }
  }
}
```

---

## 11. Negotiation Protocol

### 11.1 Overview

The negotiation protocol enables two or more agents to coordinate on a planned action before execution. It is used when:
- The action affects a shared resource or environment
- The action requires complementary behaviour from another agent (e.g., COLREGs)
- Unilateral action would create risk or conflict

### 11.2 Initiating Negotiation

An agent initiates negotiation by:
1. Detecting a condition requiring coordination (via CEP alert or reasoning)
2. Identifying the relevant peer agent(s)
3. Formulating a PROPOSE with proposed and requested actions
4. Setting a realistic `proposal_ttl_s` based on urgency

The `proposal_ttl_s` MUST account for round-trip latency on the underlying link. On satellite with 600ms RTT, a 30 second TTL gives approximately 25 exchange cycles maximum.

### 11.3 Fallback Actions

Every PROPOSE MUST include a `fallback` block specifying autonomous action if no agreement is reached before `proposal_ttl_s`. The fallback action MUST be:
- Safe (reduces risk rather than increasing it)
- Executable unilaterally
- Documented in the PROPOSE for peer awareness

### 11.4 Multi-Party Negotiation

For negotiations involving more than two agents, the initiator sends PROPOSE to multiple receivers simultaneously. Each receiver responds independently. The initiator MUST NOT execute until all required agreements are received, or until fallback triggers.

### 11.5 Negotiation Constraints

Agents MUST NOT:
- Send more than one unresolved PROPOSE on the same subject simultaneously
- Change their committed action after sending AGREE without sending RETRACT first
- Execute a PROPOSED action before receiving AGREE from all required parties

Agents MUST:
- Execute their fallback action if proposal_ttl expires without agreement
- Log all negotiation exchanges in the decision journal
- Report negotiation outcome via CONFIRM or FAIL after execution

### 11.6 Human Authority in Negotiation

At any point in a negotiation, a human operator may intervene. The `human_override_path` defined in the AID, when set to true, MUST:
1. Immediately suspend all pending proposals sent by this agent
2. Send RETRACT for any outstanding PROPOSE messages
3. Send RESUME for any active DELEGATE agreements
4. Cease all actuation until human_override_path returns to false

This is not negotiable. No peer can override human authority.

---

## 12. Control Delegation

### 12.1 Purpose

Control delegation allows an agent to temporarily transfer authority over a set of control paths to another agent. This is used for:
- Handing off tactical control while retaining strategic oversight
- Allowing a specialist agent to take over during its domain of expertise
- Graceful degradation when an agent needs to go offline

### 12.2 Delegation Constraints

A delegator:
- Can only delegate paths listed in its own `authority_scope`
- Cannot delegate more authority than it holds
- Retains ultimate responsibility for delegated actions
- Can revoke at any time by sending RESUME

A delegatee:
- MUST verify the delegator has authority over the delegated paths
- MUST enforce all `constraints` in the DELEGATE message
- MUST monitor `handback_trigger` conditions continuously
- MUST NOT sub-delegate without explicit permission from the original delegator

### 12.3 Delegation Chain

Delegation chains are permitted up to depth 2. A delegated agent MAY delegate to a third agent only if the original DELEGATE contained `allow_sub_delegation: true`.

The full delegation chain MUST be preserved in all CM Messages from sub-delegated agents so authority can be audited.

### 12.4 Authority Conflict Resolution

If two agents simultaneously claim authority over the same control path:
1. Sovereign agent takes precedence over federated agent
2. Direct authority takes precedence over delegated authority
3. Higher trust score takes precedence between equal classes
4. If still tied — BLOCK both and escalate to human

---

## 13. Transport Bindings

### 13.1 NATS JetStream (Primary)

NATS JetStream is the RECOMMENDED transport for ΣBUS CM deployments. It provides:
- Persistent message delivery with configurable retention
- At-least-once and exactly-once delivery semantics
- Native wildcard subscriptions
- Lightweight binary protocol
- Embedded server option (runs on Raspberry Pi 5 with <50MB RAM)

**Subject mapping:**

| CM Subject | NATS Subject |
|---|---|
| `cm.{platform}.broadcast` | `SIGMABUS.{platform}.CM.BROADCAST` |
| `cm.{platform}.{agent_uid}` | `SIGMABUS.{platform}.CM.{agent_uid}` |
| `cm.{platform}.role.{role}` | `SIGMABUS.{platform}.CM.ROLE.{role}` |
| Data path | `SIGMABUS.{path_with_dots_as_dots}` |

**JetStream stream configuration:**

```
Stream: SIGMABUS
  Subjects: SIGMABUS.>
  Retention: WorkQueuePolicy
  MaxAge: 24h (data), 168h (CM messages)
  Replicas: 1 (single node) or 3 (cluster)
  Storage: File (persistent) or Memory (ephemeral)
```

**Serialisation:** JSON (REQUIRED), FlatBuffers (OPTIONAL for high-frequency data streams)

### 13.2 MQTT (Alternative)

MQTT is supported for compatibility with existing maritime and IoT deployments.

**Topic mapping:**

| CM Subject | MQTT Topic |
|---|---|
| `cm.{platform}.broadcast` | `sigmabus/{platform}/cm/broadcast` |
| `cm.{platform}.{agent_uid}` | `sigmabus/{platform}/cm/{agent_uid}` |
| Data path | `sigmabus/{path_with_dots_as_slashes}` |

MQTT QoS MUST be 1 (at-least-once) for CM Messages. QoS 0 is permitted for high-frequency data streams. MQTT 5.0 is RECOMMENDED over 3.1.1 for message expiry and correlation data support.

### 13.3 ZeroMQ (Local IPC)

ZeroMQ is RECOMMENDED for intra-platform agent-to-agent communication where latency is critical and persistence is not required.

Pattern: PUB/SUB for broadcasts, DEALER/ROUTER for directed messages.

### 13.4 Serial / Bandwidth-Constrained Links

For HF radio, satellite links, or serial connections:

- HEARTBEAT interval SHOULD be increased to 60–300 seconds
- All messages MUST be compressed (zstd or lz4)
- Binary FlatBuffers serialisation MUST be used
- Message filtering at gateway level is REQUIRED — only ALERT and PROPOSE cross by default
- Sequence numbers MUST be used to detect message loss
- A store-and-forward queue MUST be maintained during link outage

Minimum viable message set for a 300 baud link:
- HEARTBEAT (compressed: ~40 bytes)
- ALERT (compressed: ~80 bytes)
- PROPOSE / AGREE / REFUSE (compressed: ~120 bytes)

---

## 14. Security

### 14.1 Signing

All CM Messages MUST be signed. The signature covers the entire message payload (excluding the `signature` field itself) serialised as canonical JSON.

Algorithm: ed25519 (REQUIRED)  
Key size: 256 bits  
Signature: base64url-encoded, included in message `signature` field

Receiving agents MUST verify signatures on:
- ANNOUNCE (always)
- DELEGATE (always)
- PROPOSE priority ≤ 2 (always)
- All other CM messages if configured for strict mode

Signature verification failure MUST cause the message to be discarded and the sending agent's trust score to be decremented by 0.50.

### 14.2 Platform Certificate Authority

Each platform MUST operate a Certificate Authority for signing sovereign agent AIDs. The CA private key MUST be stored in hardware security (TPM, HSM, or encrypted storage with hardware key). The CA public key is distributed out-of-band to peer platforms.

### 14.3 Replay Protection

All CM Messages MUST include a timestamp (`timestamp_us`). Messages with timestamps outside ±300 seconds of the receiver's local time MUST be rejected.

All CM Messages MUST include a `msg_id` (UUID). Receivers MUST maintain a replay cache of processed `msg_id` values for at least 600 seconds and MUST reject duplicates.

### 14.4 Isolation

The following MUST NOT cross platform boundaries without explicit authorisation:
- Raw sensor data streams
- Internal platform command paths (`cmd.*`)
- Platform CA private keys
- Agent private keys

### 14.5 Rate Limiting

Agents MUST enforce rate limits on incoming CM Messages per sender:

| Message Type | Default Rate Limit |
|---|---|
| HEARTBEAT | 1 per 5 seconds |
| ANNOUNCE | 1 per 30 seconds |
| QUERY | 10 per second |
| PROPOSE | 5 per second |
| ALERT | 20 per second |

Exceeding rate limits MUST result in message discard and a trust decrement.

---

## 15. Conformance

### 15.1 Conformance Levels

Three conformance levels are defined:

**Level 1 — Minimal**  
Required for any agent claiming ΣBUS CM compliance.

- MUST implement ANNOUNCE, WITHDRAW, HEARTBEAT
- MUST implement QUERY, INFORM
- MUST wrap all messages in Semantic Envelope
- MUST maintain peer registry
- MUST enforce trust class filtering
- MUST sign all CM Messages with ed25519
- MUST implement mDNS discovery OR bus-based discovery

**Level 2 — Standard**  
Required for agents participating in operational coordination.

All Level 1 requirements, plus:
- MUST implement REQUEST, CONFIRM, FAIL
- MUST implement PROPOSE, AGREE, REFUSE, RETRACT
- MUST implement ALERT
- MUST implement conversation state machines
- MUST enforce proposal_ttl and execute fallback actions
- MUST maintain conversation history log
- MUST implement trust modifiers and decay
- MUST enforce human_override_path

**Level 3 — Gateway**  
Required for agents federating between platforms.

All Level 2 requirements, plus:
- MUST implement DELEGATE, RESUME
- MUST implement cross-boundary message filtering
- MUST implement link-state-aware message adaptation
- MUST implement store-and-forward for intermittent links
- MUST implement platform CA and certificate verification

### 15.2 Declaring Conformance

An agent declares its conformance level in its AID `capabilities.cm_message_types` field and by including `cm_conformance_level: 1|2|3` in its AID `identity` block.

---

## 16. Relation to Existing Standards

### 16.1 OSI Model

ΣBUS CM occupies Layer 8 (Semantic Envelope) and Layer 9 (Negotiation) in an extended OSI framing. It explicitly depends on Layers 1–7 for transport and makes no assumptions about their implementation.

### 16.2 Signal K

Signal K provides the data path addressing convention and application-layer data formats that ΣBUS CM builds upon. Signal K paths are valid ΣBUS paths with the platform prefix prepended. ΣBUS CM does not replace Signal K — it adds the agent coordination layer above it.

### 16.3 NMEA 0183 / 2000

NMEA defines instrument data formats at Layer 6–7. ΣBUS ingestors PARSE NMEA and produce ΣBUS Semantic Envelopes. NMEA is a source format, not a peer protocol.

### 16.4 MAVLink

MAVLink defines the autopilot command protocol. ΣBUS agents issue commands that are translated to MAVLink by a bridge component. MAVLink is a target format for the actuator layer.

### 16.5 FIPA-ACL

ΣBUS CM draws conceptual inspiration from FIPA-ACL (1997), the Foundation for Intelligent Physical Agents Agent Communication Language. The message vocabulary (INFORM, REQUEST, PROPOSE, AGREE, REFUSE) derives from FIPA-ACL speech act theory. ΣBUS CM differs in being designed for resource-constrained hardware, intermittent connectivity, and physical safety requirements that FIPA-ACL did not address.

### 16.6 W3C PROV

The Semantic Envelope provenance model is conceptually aligned with W3C PROV-O. ΣBUS does not implement PROV-O directly (it is too heavyweight) but the `derived_from`, `path_history`, and `source_id` fields map to PROV concepts of `wasDerivedFrom`, `wasAttributedTo`, and `wasGeneratedBy`.

---

## 17. Design Rationale

### 17.1 Why a new protocol?

Existing agent frameworks (LangChain, AutoGen, CrewAI) treat communication as an implementation detail — each framework uses its own internal calling convention and none define a wire protocol that enables interoperability between frameworks or between agents running on different hardware. ΣBUS CM is the missing interoperability layer.

### 17.2 Why trust decay?

Static trust models fail in practice. A sensor that was reliable yesterday may be faulty today. An agent that has performed well in calm conditions may fail in extreme ones. Trust must reflect the current reality of the system, not its history alone. Decay ensures that trust must be continuously earned, not assumed from past performance.

### 17.3 Why mandatory provenance?

In safety-critical autonomous systems, the question "why did the system do that?" must always be answerable. Provenance embedded in every message makes auditability a structural property rather than an afterthought. Every decision can be traced back to its sensor inputs, their trust scores at the time, and the reasoning chain that led to action.

### 17.4 Why FlatBuffers as binary option?

Cap'n Proto and Protocol Buffers were also considered. FlatBuffers was selected for its zero-copy read semantics (critical for high-frequency data streams on memory-constrained hardware) and its compatibility with Rust, C++, and Python without code generation complexity. JSON remains the primary format for debuggability.

### 17.5 Why NATS JetStream as primary transport?

NATS was selected over Kafka (too heavyweight for edge), Redis Streams (no native fan-out), and raw MQTT (no persistence semantics) for its combination of lightweight deployment, persistent streams, native wildcard subscriptions, and an embedded server that runs in <50MB RAM on a Raspberry Pi 5.

---

## Appendix A — JSON Schemas

See `schemas/aid.schema.json` and `schemas/cm-message.schema.json` in this repository.

---

## Appendix B — Example Conversations

See `examples/` directory:
- `02-collision-avoidance.md` — Full PROPOSE / AGREE negotiation trace

---

## Appendix C — Glossary

See [Terminology](#2-terminology) and inline definitions throughout this document.

---

## Appendix D — Change Log

| Version | Date | Changes |
|---|---|---|
| 0.1 | 2025-05-18 | Initial working draft |

---

*ΣBUS CM Specification — Draft v0.1*  
*Released under GNU General Public License v3.0*  
*Contributions welcome via pull request*

# ΣBUS / Sigma Bus v0.1
## A coherent interaction, stream, and metadata substrate for AI, LLMs, agents, and autonomous systems

**Status:** Concept architecture draft  
**Project role:** Cognitive Matrix protocol family; Omni-AI can host a practical implementation layer  
**Core idea:** Every useful observation, stream, tool, screen, agent capability, and action becomes a typed, metadata-rich object in a common matrix that can be routed, reasoned over, verified, and acted upon.

---

## 1. Why ΣBUS exists

Most agent systems are built around:

- `LLM -> tool/API -> result`
- `agent -> workflow -> output`

That is useful, but incomplete.

A true autonomous system must also handle:

- Legacy software with no API
- Windows desktop applications, file managers, marine tools, IDEs, and browser UIs
- Multiple windows and displays with different contexts active at once
- Continuous streams: sensors, NMEA, CAN, AIS, RF/SDR, cameras, logs, banking-style transaction feeds, system telemetry
- Agent-to-agent coordination
- Provenance, trust, data freshness, timing, and action authority
- Reversible and verifiable system actions

**ΣBUS** is the missing substrate between raw reality and agent reasoning.

It is not only a message bus. It is a **semantic event and interaction matrix**.

---

## 2. Naming

### Recommended naming hierarchy

- **ΣBUS / Sigma Bus** — the protocol family and conceptual architecture
- **ΣMatrix / Sigma Matrix** — the live in-memory runtime graph of active streams, entities, agents, and state
- **Omni-Bus** — the Omni-AI implementation/profile of ΣBUS for your local systems
- **CM-Σ** — the Cognitive Matrix module that uses ΣBUS as its sensory/interaction substrate

### Meaning of Σ

The symbol `Σ` is appropriate because the system is the **sum of all streams**, but also because it implies:

- Summation
- Aggregation
- Fusion
- State reconstruction
- Cross-domain synthesis

---

## 3. The fundamental design claim

**A system becomes cognitively useful when it can identify, normalize, preserve, and reason over flows of state — not merely call tools.**

ΣBUS therefore treats these as first-class citizens:

1. **Streams** — continuous or discrete data flows
2. **Entities** — vessels, processes, screens, files, accounts, emitters, sensors, agents
3. **Events** — state changes, detections, alerts, user actions, system actions
4. **Artifacts** — reports, snapshots, signal captures, images, files, reasoning outputs
5. **Actions** — API calls, UI clicks, control messages, workflow invocations
6. **Metadata** — provenance, timing, confidence, policy, retention, identity, relationships

---

## 4. OSI-inspired Sigma Stack

This is not a networking stack clone. It is a **layered cognitive interaction model**.

| Layer | Name | Purpose |
|---|---|---|
| L0 | Substrate | Physical devices, hosts, clocks, storage, displays, sensors |
| L1 | Capture | Screenshots, UI trees, files, SDR IQ, NMEA, logs, APIs, webhooks |
| L2 | Transport & Envelope | Event movement, persistence, replay, event envelopes |
| L3 | Metadata & Identity | Provenance, schema IDs, trust, tags, retention, authority |
| L4 | Semantic Normalization | Convert raw inputs into shared entities, events, intents |
| L5 | Context & Memory | Live state graph, indexes, RAG, temporal memory, histories |
| L6 | Agent & Policy | LLMs, crews, Codex, AnythingLLM, policy gates, planners |
| L7 | Action & Verification | UI actions, API calls, automation, autonomous control, post-checks |

---

## 5. ΣBUS object model

### 5.1 ΣFrame — canonical event envelope

A `ΣFrame` is the common envelope for observations, events, and actions.

```json
{
  "sigma_version": "0.1",
  "frame_id": "uuid",
  "frame_type": "observation | event | action | artifact | state",
  "stream_id": "desktop.win.screen.01",
  "source_id": "host.windows.main",
  "schema_id": "sigma.desktop.window_state.v1",
  "observed_at": "2026-05-18T14:28:10.231+02:00",
  "emitted_at": "2026-05-18T14:28:10.245+02:00",
  "sequence": 91392,
  "correlation_id": "task-xyz",
  "payload_ref": "inline | blob://... | file://... | sigmf://...",
  "metadata": {},
  "payload": {}
}
```

ΣFrame should be compatible in spirit with established event-envelope thinking, but tailored for cognitively meaningful agent systems.

---

### 5.2 ΣCard — identity/capability manifest

A `ΣCard` describes a source, agent, tool, device, process, or stream producer.

Example roles:

- `agent.desktop_operator`
- `sensor.ais_receiver`
- `stream.sdr.rf_frontend`
- `tool.total_commander_adapter`
- `service.anythingllm_agent_skill`

Example fields:

```json
{
  "sigma_card_version": "0.1",
  "id": "agent.desktop_operator.win01",
  "kind": "agent",
  "name": "Windows Desktop Interaction Agent",
  "capabilities": [
    "desktop.observe",
    "desktop.ui_tree.read",
    "desktop.screenshot.read",
    "desktop.pointer.click",
    "desktop.keyboard.type",
    "desktop.ahk.execute",
    "desktop.verify_state"
  ],
  "authority": {
    "read": ["desktop", "window_tree", "screenshot"],
    "write": ["keyboard", "mouse", "approved_ahk_scripts"],
    "blocked": ["credential_exfiltration", "silent_destructive_batch_ops"]
  },
  "transport": ["mcp", "local_rpc", "a2a_bridge"],
  "trust_level": "local_supervised",
  "owner": "omni-ai"
}
```

`ΣCard` is analogous in spirit to an agent capability card, but generalized beyond agents to **all active participants in the matrix**.

---

### 5.3 ΣTags — metadata layer

This is the “NTFS-like metadata layer” concept generalized to live streams.

Every stream, frame, entity, artifact, and action can carry structured tags.

#### Recommended tag families

**Identity**
- `source_id`
- `stream_id`
- `entity_id`
- `schema_id`
- `origin_agent`

**Time**
- `observed_at`
- `emitted_at`
- `event_time`
- `processing_time`
- `ttl`
- `stale_after`

**Provenance**
- `captured_by`
- `derived_from`
- `transform_chain`
- `hash`
- `storage_pointer`

**Trust and confidence**
- `sensor_confidence`
- `classification_confidence`
- `agent_confidence`
- `human_verified`
- `source_reputation`

**Policy**
- `sensitivity`
- `retention_class`
- `allowed_consumers`
- `action_authority`
- `requires_confirmation`

**Semantic meaning**
- `domain`
- `modality`
- `units`
- `ontology_type`
- `mission_relevance`

**Cognitive signals**
- `novelty_score`
- `priority`
- `attention_state`
- `anomaly_score`
- `memory_class`

---

## 6. Desktop Interaction Agent: the first practical ΣBUS skill

### 6.1 The idea

The desktop agent is not just an AutoHotkey script generator. It is a **computer-use subsystem** that can:

1. Observe what is on screen
2. Understand active apps, windows, controls, files, and text
3. Plan a deterministic action sequence
4. Execute through the most reliable control path available
5. Verify the resulting state
6. Emit every step into ΣBUS

### 6.2 Control hierarchy

Use the most reliable layer first:

1. **Native/API/CLI path** — when software exposes it
2. **UI Automation/accessibility tree** — inspect controls and invoke actions programmatically
3. **Window/process metadata** — active window, titles, focus, menus, clipboard, dialogs
4. **Vision/screenshot parsing** — fallback for non-semantic or legacy UIs
5. **AutoHotkey/input synthesis** — clicks, keys, hotkeys, scripted macros
6. **Human escalation** — when confidence is low or operation is high-risk

### 6.3 Desktop skill capabilities

Proposed skill namespace:

- `desktop.observe`
- `desktop.list_windows`
- `desktop.inspect_window`
- `desktop.capture_screenshot`
- `desktop.read_ui_tree`
- `desktop.find_text`
- `desktop.find_control`
- `desktop.click`
- `desktop.type`
- `desktop.hotkey`
- `desktop.run_ahk`
- `desktop.verify`
- `desktop.record_demonstration`
- `desktop.replay_with_adaptation`

### 6.4 Action loop

```text
Observe -> Parse -> Select target -> Execute -> Verify -> Commit to ΣBUS
```

Example:

```text
Goal: Export selected files from Total Commander to a project folder.

1. Observe active window and UI tree
2. Confirm Total Commander is focused
3. Identify selected files and destination pane
4. Choose safe operation sequence
5. Execute hotkey / menu action / AHK macro
6. Verify destination folder changed as expected
7. Emit action artifact + before/after state
```

### 6.5 Why this matters

This lets an agent operate:

- Total Commander / Norton Commander-style file workflows
- Router control panels
- Legacy industrial software
- Windows simulators
- Marine utilities
- IDEs and developer tools
- Configuration GUIs with no API

---

## 7. Can LLMs handle screenshots, windows, and mixed interfaces?

### 7.1 Yes, but not by raw brute force

Modern multimodal systems can read screenshots and reason about UI elements. However, robust autonomy should not depend on asking a large model to interpret full-resolution desktop frames continuously.

ΣBUS should use a **tiered perception strategy**:

- Cheap always-on watchers for process/window/event changes
- UI Automation tree whenever available
- Screen-diff and region-diff capture instead of full constant frames
- OCR or UI screenshot parsing where necessary
- Local classification/summarization for repetitive states
- Escalation to a stronger multimodal model only when ambiguity or decision value is high

### 7.2 Multiple screens or multiple windows

Treat each monitor and each top-level window as a **registered stream**:

- `desktop.monitor.0.frame`
- `desktop.monitor.1.frame`
- `desktop.window.total_commander.state`
- `desktop.window.openocpn.state`
- `desktop.window.router_webui.state`

ΣBUS stores:

- Current snapshot
- Last change timestamp
- Focus state
- Window geometry
- App identity
- Detected text/UI controls
- Agent attention score

The LLM should not receive “everything always.” It should receive the **relevant state slice**.

---

## 8. Continuous data streams: how ΣBUS registers and processes them

### 8.1 General stream lifecycle

```text
Register -> Observe -> Normalize -> Enrich -> Route -> Persist -> Reason -> Act
```

### 8.2 Stream registration

Every data source creates a `ΣCard` and registers one or more streams:

```json
{
  "stream_id": "rf.sdr.frontend01.iq",
  "source_id": "device.sdr.01",
  "schema_id": "sigma.rf.iq_stream.v1",
  "modality": "rf",
  "sampling": {
    "sample_rate": 2400000,
    "center_frequency": 162000000
  },
  "retention": "ring_buffer_30s",
  "downstream": ["burst_detector", "classifier", "sigmf_archiver"]
}
```

### 8.3 Processing stages

1. **Raw capture** — store or buffer source data
2. **Feature extraction** — compute cheap structured facts
3. **Detection/classification** — identify salient events
4. **Correlation** — relate to known entities, locations, prior patterns
5. **Agent summary** — create human/LLM-friendly event summaries
6. **Action or memory update** — alert, investigate, store, ignore, escalate

---

## 9. Example: banking-style transaction stream

A transaction system is useful as a mental model because it must preserve:

- Order
- Identity
- Provenance
- Replayability
- Duplication control
- Auditability
- Timely decisions

### 9.1 Example ΣFrame

```json
{
  "frame_type": "event",
  "stream_id": "finance.tx.authorized",
  "schema_id": "sigma.finance.transaction_authorized.v1",
  "payload": {
    "transaction_id": "tx-9831",
    "account_ref": "acct-tokenized",
    "amount": 72.40,
    "currency": "EUR",
    "merchant_ref": "merchant-tokenized",
    "channel": "card_present",
    "risk_score": 0.12
  },
  "metadata": {
    "retention_class": "regulated",
    "confidence": 1.0,
    "requires_exactly_once_state_update": true,
    "audit_chain": "ledger-event-pointer"
  }
}
```

### 9.2 What agents receive

Agents should not reason over raw payment firehoses by default. They receive:

- Derived anomalies
- Reconciliation mismatches
- Duplicate suspicion
- Counterparty changes
- Unexpected velocity patterns
- Summaries with traceable references back to original events

---

## 10. Example: SIGINT / SDR stream

### 10.1 Key distinction

Raw IQ samples are too large and too low-level for direct LLM reasoning. The LLM should reason over **derived signal events**, with pointers back to recorded evidence.

### 10.2 Recommended flow

```text
SDR IQ -> Ring buffer -> DSP feature extractor -> Burst detector -> Classifier -> ΣFrame event -> Agent investigation
```

### 10.3 Example RF events

- `rf.burst.detected`
- `rf.signal.classified`
- `rf.emitter.track.updated`
- `rf.ais_like_packet.detected`
- `rf.unrecognized_pattern.persistent`

### 10.4 Metadata bridge

Use rich signal metadata concepts:

- Frequency
- Sample rate
- Time range
- Equipment identity
- Capture location
- Modulation guess
- Confidence
- Artifact pointer

A Sigma RF artifact can point to a SigMF-style recording or another standardized RF evidence bundle.

---

## 11. Agent integration model

ΣBUS does not replace agent frameworks. It supports them.

### 11.1 AnythingLLM

Use:

- Custom agent skills
- MCP compatibility
- Agent flows

Potential role:

- Human-facing local interface to ΣBUS
- Query agent over indexed stream summaries, files, and entities
- Trigger safe local skills

### 11.2 CrewAI

Use:

- Agents for specialized roles
- Flows for event-driven pipelines
- Memory for structured context

Potential role:

- Investigation crews
- Classification crews
- Maintenance crews
- Report-generation crews

### 11.3 Codex / coding agents

Use:

- Code generation and adapter creation
- Reverse engineering of interfaces and formats
- Building bridges, parsers, schemas, and skills
- Maintaining ΣBUS registries and adapters

### 11.4 MCP

Use MCP as:

- Tool/data exposure layer
- Local/remote capability connection format

ΣBUS can expose itself through MCP resources and tools.

### 11.5 A2A

Use A2A as:

- Agent-to-agent communication and delegation
- Remote agent capability discovery
- Cross-system collaboration

ΣBUS can publish agent and node capability summaries into A2A-facing agent cards.

---

## 12. Practical architecture for Omni-AI / Cognitive Matrix

### 12.1 Core services

1. **Sigma Registry**
   - Stores ΣCards, schemas, stream definitions, permissions

2. **Sigma Event Bus**
   - Ingests and routes ΣFrames
   - Local-first and replayable

3. **Sigma State Graph**
   - Current state of entities, sources, agents, streams, tasks

4. **Sigma Archive**
   - Files, SigMF artifacts, screenshots, reports, traces

5. **Sigma Policy Engine**
   - Authority, confirmation gates, data retention, redaction

6. **Sigma Agent Gateway**
   - MCP adapters
   - A2A bridge
   - AnythingLLM/CrewAI/Codex tool surfaces

7. **Sigma Desktop Operator**
   - Windows UI control, observation, AHK execution, verification

---

## 13. Suggested MVP path

### Phase 1 — Spec and object contracts

- Define `ΣFrame`
- Define `ΣCard`
- Define core metadata families
- Define stream registration format
- Define authority/policy tags

### Phase 2 — Event bus and registry

- Implement a local registry
- Implement event persistence/replay
- Start with lightweight transport suitable for edge systems

### Phase 3 — Desktop Operator skill

- Build Windows-side observation/control daemon
- Expose through local RPC and MCP
- Add AutoHotkey bridge
- Add UI Automation tree support
- Add screenshot capture and state verification

### Phase 4 — Omni-AI integration

- Register existing Omni-AI services as ΣCards
- Publish SMTIS, system health, tactical feed status, service logs as ΣFrames
- Add AnythingLLM query skill

### Phase 5 — Cognitive Matrix stream intake

- Add memory categorization and novelty scoring
- Add event correlation and “preserve unique outliers” policy
- Add dream/offline consolidation metadata using your existing CM memory-layer concept

### Phase 6 — SDR / marine / sensor fusion

- Register AIS, SDR, telemetry, LoRa, GNSS, vision detections
- Build RF event summaries and artifact pointers
- Add cross-domain correlation

---

## 14. Core design principles

1. **Observe before acting**
2. **Prefer structured control; use pixels only when needed**
3. **Every action is logged, linked, and verifiable**
4. **Streams are not just data; they are registered semantic citizens**
5. **Metadata is not optional; metadata is the memory of the system**
6. **LLMs reason over relevant slices, not raw firehoses**
7. **Agents should advertise capabilities and authority clearly**
8. **Outliers must be preserved, not compressed away**
9. **Human oversight is a policy state, not a missing feature**
10. **ΣBUS should support both local edge autonomy and future distributed coordination**

---

## 15. Recommended first skill name

### `sigma.desktop-operator`

Or, if you want a more Omni-AI-flavored implementation name:

### `omni.desktop-pilot`

Recommended positioning:

> A local-first desktop interaction agent that observes Windows UI state, operates applications through structured UI automation and deterministic input synthesis, verifies outcomes, and emits every observation/action as ΣBUS frames.

---

## 16. Short canonical definition

> **ΣBUS is a semantic stream and interaction substrate for autonomous AI systems. It registers every source, screen, stream, agent, and action through typed envelopes and metadata, then exposes that matrix to LLMs and agents for reliable reasoning, coordination, and verified control.**

---

## 17. Reference families worth building around

- Computer-use agents and screenshot-to-action loops
- Windows UI Automation and AutoHotkey-style deterministic actuation
- UI parsers and screenshot grounding models
- MCP for tool/data exposure
- A2A for agent-to-agent interoperability
- CloudEvents-like event envelopes
- OpenTelemetry-style semantic conventions and observability
- Kafka/NATS-style streaming, persistence, replay, and delivery semantics
- SigMF and GNU Radio concepts for RF metadata, stream tags, and message conversion


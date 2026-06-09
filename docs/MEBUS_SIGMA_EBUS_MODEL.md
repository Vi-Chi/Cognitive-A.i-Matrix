# MEBUS = Sigma + EBUS — canonical model & coverage map

**Source:** owner (Vi) corrections in the 2026-06-07 Codex session
(`_Documentation/codex chat raw.txt`, `chat_export_mebus_sigma_ebus_2026-06-07.md`) +
`sigmabus/{SIGMABUS-CORE-SPEC.mdc, SIGMABUS-LLM-SPEC.mdc, SIGMABUS-LLM.md, sigma-bus-cognitive-matrix-v0.1.md}`.
**Status:** reconciliation captured; **no broker code built** (owner told Codex "schema/docs first,
no broker build yet" — this honours that).

## 1. The correction (authoritative, from the owner)

> "MEBUS is not only a protocol for data streams… it is advanced AI identification and translation,
> an AI **job handler and broker**." · "**MEBUS = Sigma and EBUS**."

MEBUS is **not** "the message bus." It is the common operating fabric for events, jobs, model
providers, sensors, memory records, audits, tools, and actions:

| Half | = | Provides |
|------|---|----------|
| **Sigma (Σ)** | semantic **identity** plane | AID, ΣFrame/SemanticEnvelope, meaning, provenance, trust, uncertainty, capability, authority, schema, **translation/normalisation**, MatrixRegistry |
| **EBUS** | **Event Bus** runtime | ingest, pub/sub, route, **persist, replay**, trigger, watchdogs, event streams, **job envelopes**, provider dispatch/execution, outcome return |

> Naming note: the GitHub repo reads **M = Membrane** ("Membrane Sigma Bus"); this session reads
> **M-protocol Event BUS**. Both resolve as **MEBUS = Membrane(Sigma + EBUS)** with **EBUS = Event
> Bus** now firm. The **M expansion (Membrane / M-protocol / Memory) remains the owner's open call.**

## 2. Provider federation (the newly-emphasised dimension)

External models — Claude, OpenAI, Grok, Google, **NVIDIA Nemotron**, local Ollama, Hailo workers —
are **MEBUS participants ("providers"), not rulers**: *witnesses, specialists, critics, collaborators
— providers, not sensory truth.* Each gets an AID (`AID.provider.<name>`) carrying capabilities,
model/runtime info, context budget, latency/cost/privacy profile, trust history, allowed
tools/control paths, degradation path, and **provenance on every output**. **Autopoiesis** uses MEBUS
**job envelopes** to route each request: local Hailo · local CPU · remote provider · decentralized
compute · or **reject/veto**.

### LLM tier architecture (SIGMABUS-LLM-SPEC)

| Tier | Role | Example | Escalates |
|------|------|---------|-----------|
| 0 | rules / CEP + cached pattern-match | — | — |
| 1 | small / Hailo safety watchdog (~200 ms) | Phi-3-mini | →2 via UNCERTAINTY when entropy > θ |
| 2 | local reasoning (nav/collision) | Qwen2.5-7B q4 | →3 only for safety-critical / multi-day / all-Tier-2 trust < 0.60 |
| 3 | sovereign / cloud, full DELEGATE authority | Claude / GPT-4o | never (terminal; escalation loops = defect) |

Degradation chain: `online→T3 · link-lost→T2 · CPU-load→T1 · critical→T0`. All tiers offline-capable;
cloud optional. Confidence < 0.70 ⇒ emit UNCERTAINTY, do **not** act.

### Broker speech-acts (extend the cm.* vocabulary)

`CONTEXT_SHARE · UNCERTAINTY · CRITIQUE · CAPABILITY_PROBE · DECOMPOSE · SYNTHESIZE`.
Orchestration patterns: **star** (DECOMPOSE → REQUEST each specialist → SYNTHESIZE) and **debate**
(identical REQUEST to N providers → SYNTHESIZE).

## 3. Coverage map — what the current build has vs. what this reveals as missing

| Layer | Element | Built? |
|-------|---------|--------|
| Sigma | ΣFrame/SemanticEnvelope (= `MMessage` 7-field) | ✅ `protocol.py` |
| Sigma | AID identity + trust classes + ed25519 (HMAC ref) | ✅ `coordination.py` |
| Sigma | effective-trust gate + freshness | ✅ `protocol.py` |
| Sigma | translation / normalisation (adapters) | ✅ `adapter*.py` (JSON, SignalK, NMEA) |
| Sigma | m.* cognition payload + PredictionRecord | ✅ `cognition.py`, `records.py` |
| Sigma | cm.* coordination (15 types, negotiation) | ✅ `coordination.py` |
| **EBUS** | pub/sub + Ω₈-gated routing | ✅ `MembraneBus` |
| **EBUS** | **event persistence + replay** | ❌ |
| **EBUS** | **MatrixRegistry** (stream/source registry; reject-unregistered strict mode) | ❌ |
| **EBUS** | **job envelopes + provider dispatch + outcome return** | ❌ |
| **EBUS** | watchdogs / triggers / CEP | ❌ |
| **Broker** | provider AIDs (`AID.provider.*`) + capability/cost/latency/trust descriptors | ⚠️ AID supports it (`role`, `federated`/`claimed`); provider profile fields not modelled |
| **Broker** | LLM tiers 0–3 + UNCERTAINTY escalation cascade | ❌ |
| **Broker** | broker speech-acts (CONTEXT_SHARE/CRITIQUE/CAPABILITY_PROBE/DECOMPOSE/SYNTHESIZE) | ❌ |
| **Broker** | Autopoiesis job routing / veto | ❌ (lives in Autopoiesis repo) |

**Summary:** the build covers the **Sigma half** well and the **EBUS half** only at the pub/sub
level. The **broker / provider-federation** dimension and **persistence/replay/registry/jobs** are
the real frontier this session surfaced.

## 4. Scope reframe (owner)

The **A.i engine / AGI substrate is the primary project**; **Vento-Vivere / Wibo 835** is the
embodied proving ground & future test environment (not the root); **CM5-Hailo** is the next compute
body; **RPi4** is prototype/history; Multiboot/Easy2boot is out of scope. Owner build sequence:
**AnythingLLM-style grounded-knowledge interface → MEBUS core → Urbi & Orbi → test against
Autopoiesis + the Nemotron/provider-federation concept.** Constraint: **"no placeholders or
simulations"** — real docs, real reasoning traces, real audit records.

## 5. Recommended next work (documentation-first, per owner)

1. `MEBUS_PROJECT_DECISIONS.md` — lock: MEBUS = Sigma + EBUS; decide the **M** expansion; SigmaBus
   nested under MEBUS; provider-federation in-scope.
2. Schema-first for the EBUS/broker layer: **ProviderAID** profile, **JobEnvelope**, the 6 broker
   speech-acts, the MatrixRegistry record — *before* implementation.
3. Only then: build EBUS persistence/replay + registry + the provider/tier broker (the part Codex
   was asked to defer).

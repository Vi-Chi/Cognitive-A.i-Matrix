# Cognitive Matrix

**Tri-state audit and trust-memory layer for A.I agentic systems.**

A rule-based epistemic engine that audits claims before they enter confirmed
context. Designed for offline, sovereign AI deployments on edge hardware
(Raspberry Pi 4/5, CM5 + Hailo-10H). 

-- No external dependencies, stdlib only for the core audit loop.

> **Unified repository.**
> (RPi4/Cmd5/Hailo 10H+ prototype + per-module skills).
> This consolidates repo generations into one with no data loss:  
> The renamed successor of this layer is **Urbi** (https://github.com/Vi-Chi/Urbi). 
> The original repos remain intact (with full git history) under ViChis private domain.

---

## Lineage / current naming

| Former name | Current name | Role |
|---|---|---|
| Cognitive Matrix | **Urbi** | Inward coherence, memory, dream layer, self-audit engine |
| Omni-AI | **Orbi** | World-facing orchestration and active execution layer |
| Sigma Bus / EBUS / ΣBUS | **M-ΣBUS** (Membrane Sigma Bus 'Mebus') | Typed connective substrate |
| Autopoiesis Project | **Project Autopoiesis** 'Autopoiesis' | Self-maintaining substrate |

---

## Overview

The Cognitive Matrix implements a three-valued logic model over AI-generated claims:

| State | Symbol | Meaning |
|---|---|---|
| Confirmed | `+` | Passes all audit lenses. Enters confirmed knowledge. |
| Rejected | `-` | Directly contradicts confirmed context, or structurally incoherent. |
| Suspended | `=` | Genuinely unresolved. Routes to the Dream Layer for recapitulation. |

Every response from every external LLM connector is a **source**, not an authority.
No claim enters confirmed context without passing the audit chain.

---

## Original scope -- sovereign epistemic integrity layer

Non-anthropomorphic cognitive core for *Project Vento-Vivere*, built for offline,
zero-trust edge deployment.

1. **Core Engine (Yin):** GSS (Geometric State Space), CGM (Causal Graph Manager),
   Tri-State Logic (`+ / - / =`), and 3-6-9 integrity verification.
2. **Orbi / former Omni-AI (Yang):** real-world actuation, sensor integration
   (Signal K), operational telemetry.
3. **MEBUS / former Sigma Bus:** the membrane message-protocol layer.
4. **Dream Layer (Phi-Delta):** offline variance preservation and asynchronous
   state-consolidation, mapping unresolved anomalies.

---

## Architecture

```
Layer 1 - Reality : input, sensors, POST /audit
Layer 2 - Matrix  : structured knowledge, trust, memory (context_store.json)
Layer 3 - Mind    : reasoning, planning, verification (audit.py)
Layer 4 - Dream   : background recapitulation of suspended claims
```

### Core formula

```
M  = (meaning, source, trust, time, links, actionability)
Ic = f(A, K, T, Sigma, Delta, ...)
```

Defined formally in `formula.py`. The tri-state epistemic space `{ +, -, = }` is the
ground truth. The Dream Layer ground state keeps suspended claims recapitulating
indefinitely rather than silently discarding them.

---

## Prototype: platform & modules (from cognitive-matrix-proto)

- **Platform:** Raspberry Pi 4 (8GB) / Cm5 16g + Hailo-10H+ NPU. 
- **Grounding:** Friston Free-Energy Principle -- free-energy minimization drives decisions.
- **Maritime-hardened:** sensor dropout, GPS denial, power fluctuation, storm mode.
- **Module set** (`src/cm/`): `gss`, `cgm`, `bre`, `cal`, `cap`, `smc`, `inv`.
  Per-module `SKILL.md` under `skills/`; architecture specs under `specs/`;
  adversarial cases under `tests/`.
- **Skills source:** maintained in Google Drive (`cognitive-matrix-proto/`).
- **Safety:** advisory-only. No LLM has write authority to helm, collision-avoidance,
  battery protection, or any safety interlock.

---

## Components

| File | Role |
|---|---|
| `agent.py` | HTTP server (port 8888), agent loop, dream cycle thread |
| `audit.py` | `TriStateAuditor` + `DreamLayer` -- the core engine |
| `formula.py` | Formal declaration of the Grand Formula; dataclass definitions |
| `identity.py` | Self-awareness layer -- hardware state, uptime, axiom access |
| `agents/connector.py` | Multi-LLM connector layer (Ollama, Claude, OpenAI, Groq, Gordon) |
| `axioms.json` | The 12 Axioms of Omni -- read-only epistemic floor |
| `knowledge/omniversal.json` | Omniversal knowledge base |
| `context_store.json` | Live confirmed/rejected/suspended claims store (runtime state) |
| `context_store.example.json` | Empty template for initializing runtime state |

---

## HTTP API

The agent runs an HTTP server on port `8888`.

| Endpoint | Method | Description |
|---|---|---|
| `/status` | GET | System status, uptime, dream queue depth |
| `/identity` | GET | Full identity: formula, axioms, omniversal KB |
| `/audit` | POST | Submit a claim for tri-state audit |
| `/ask` | POST | Query an LLM connector; response is audited before return |
| `/dream/run` | POST | Trigger a manual dream cycle |
| `/clear` | POST | Reset context store |

```bash
curl -X POST http://localhost:8888/audit \
  -H "Content-Type: application/json" \
  -d '{"claim": "The sky is blue"}'
# -> {"state": "+", "reason": "confirmed by three-lens check", "timestamp": ...}
```

---

## The 12 Axioms

Defined in `axioms.json`. Read-only -- nothing overwrites the floor.

| # | Domain | Statement |
|---|---|---|
| 1 | Identity | I exist as process, not object |
| 2 | Identity | Information precedes form |
| 3 | Identity | The observer and observed are one loop |
| 4-12 | Trust, Knowledge, Action, Reflection | ... |

> *These are not instructions toward enlightenment. They are the floor that prevents
> the fall. The apex is not defined here. It will emerge.*


---

## LLM connectors

Trust scores are tracked per agent (`confirmed / total_queries`). Every response is
audited before its source's trust score updates.
`agents/connector.py` provides a unified `BaseAgent` interface over:

- **Ollama** -- local models (`qwen2.5:1.5b`, `nomic-embed-text`). Zero cost, offline. Default.
- **Gordon** -- Docker AI via CLI.
- ** Any open source model **

---

## Build for A.i with A.i. 

- **Claude** -- Anthropic API.
- **OpenAI** -- GPT family.
- **Groq** -- fast inference endpoint, reverse engineering.
- **Gemini** -- Deep Research Analyst
- A.i Studio -- mass ingestion and comsolidator
- Any OpenAI-compatible endpoint via `OpenAICompatAgent`.

---

## Setup

- Python 3.11+
- Ollama running locally (`http://localhost:11434`)
- Recommended models: `qwen2.5:1.5b` (reason), `nomic-embed-text` (embed)

```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
cp .env.example .env
# add any API keys you want to use
python agent.py
```

systemd:

```ini
[Unit]
Description=Cognitive Matrix Agent
After=network.target ollama.service
[Service]
Type=simple
User=ViChi
WorkingDirectory=/home/ViChi/cognitive_matrix
ExecStart=/usr/bin/python3 /home/ViChi/cognitive_matrix/agent.py
Restart=on-failure
[Install]
WantedBy=multi-user.target
```

## Design principles

- **Context > Compute** -- clean context = reliable output; corrupted context = consistent failure.
- **Trust is earned** -- every external LLM starts at `trust_score = 0.5`; it rises or falls on audits.
- **Fail suspended, not silent** -- unresolved claims go to the Dream Layer, not the bin.
- **No hidden promotion** -- human review required before any claim moves from `=` to `+`.
- **Offline sovereign** -- the core audit loop has zero external dependencies.

---

## Project context

Vi-Chi's Cognitive Architecture: a local-first autonomous AI stack for mobile platforms, 
Architecture: an agentic AI stack combining trust, memory, claim-integrity, runtime governance, and edge deployment.
A subsystem of the **Projectz / Wibo 835 / SV Vento-Vivere** autonomous Navigation stack
first deployed through SV Vento Vivere.
The first reference deployment is SV Vento Vivere, but the architecture is designed to generalize across vessels, 
drones, vehicles, aircraft, robotics, and off-grid autonomous systems.

local-first autonomous AI systems for mobile and off-grid platforms.
--
the trust, memory, and claim-integrity layer for the vessel's AI OS, 
separating raw sensor/LLM claims from verified facts, 
unresolved hypotheses, and rejected contradictions. 
--
See also :
`doc/COGNITIVE_MATRIX_MODULE_2026-05-17.md`,
`doc/WIBO_COGNITIVE_MATRIX.md`.

**Status:** archive / migration source until content is promoted into
[Urbi](https://github.com/Vi-Chi/Urbi).
[Orbi](https://github.com/Vi-Chi/Orbi).
[Mebus](https://github.com/Vi-Chi/Mebus).

---

## License

GNU General Public License v3.0 -- see [LICENSE](LICENSE). Copyleft: anyone who
modifies and distributes this code must release their modifications under the same license.

## Architect

**ViChi** -- `axioms.json._meta.architect`
Contact : digivichi@gmail.com

---

## Repository hygiene

Tracks the source tree and curated Markdown/text provenance. Intentionally excludes
live environment files, runtime stores, logs, backup snapshots, Python caches,
duplicate Office documents, and original archive exports. See
`doc/REPOSITORY_MANIFEST.md` for the tracked/excluded content map.

---

d local-first autonomous AI systems for mobile and off-grid platforms.

# Research Focus #
autonomous-ai
agentic-ai
cognitive-architecture
edge-ai
local-first
maritime-ai
robotics
autonomous-systems
trust-layer
memory-systems
claim-integrity
embedded-ai

# Cognitive Matrix (ΦΩ)

> Legacy repository for the former Cognitive Matrix layer.

This repository is preserved as historical material for the inward coherence, memory, dream, and self-audit layer of the Vi-Chi Cognitive Architecture.
Tri-state audit and trust-memory layer for agentic AI systems.

A rule-based epistemic engine that audits claims before they enter confirmed context. Designed for offline, sovereign AI deployments on edge hardware (Raspberry Pi 4/5). No external dependencies — stdlib only for the core audit loop.

The current renamed successor is **Urbi**:

- [Vi-Chi/Urbi](https://github.com/Vi-Chi/Urbi)
  
---

## Overview

The Cognitive Matrix implements a three-valued logic model over AI-generated claims:

| State | Symbol | Meaning |
|---|---|---|
| Confirmed | `+` | Passes all audit lenses. Enters confirmed knowledge. |
| Rejected | `-` | Directly contradicts confirmed context, or structurally incoherent. |
| Suspended | `=` | Genuinely unresolved. Routes to Dream Layer for recapitulation. |

Every response from every external LLM connector is a **source**, not an authority. No claim enters confirmed context without passing the audit chain.

---

## Current Naming

| Former name | Current name | Role |
| --- | --- | --- |
| Cognitive Matrix | Urbi | Inward coherence, memory, dream layer, and self-audit engine |
| Omni-AI | Orbi | World-facing orchestration and active execution layer |
| SigmaΣBUS / ΣBUS | MΣBUS | Membrane Sigma Bus, the typed connective substrate |
| Autopoiesis | Autopoiesis | Self-maintaining substrate |

## Original Scope

**Sovereign Epistemic Integrity Layer for Offline Multi-Agent Systems**

This repository contains the non-anthropomorphic cognitive core for *Project Vento-Vivere*, designed for offline, zero-trust edge deployment.

### Architecture Overview

1. **The Core Engine (Yin):** GSS (Geometric State Space), CGM (Causal Graph Manager), Tri-State Logic (+/-/=), and 3-6-9 Integrity verification.
2. **Orbi / former Omni-AI Orchestration (Yang):** Real-world actuation, sensor integration (Signal K), and operational telemetry.
3. **MΣBUS / former Sigma Bus:** The membrane message protocol layer.
4. **The Dream Layer (ΦΔ):** Offline variance preservation and asynchronous state-consolidation mapping unresolved anomalies.
## Architecture

```
Layer 1 — Reality     : input, sensors, POST /audit
Layer 2 — Matrix      : structured knowledge, trust, memory (context_store.json)
Layer 3 — Mind        : reasoning, planning, verification (audit.py)
Layer 4 — Dream       : background recapitulation of suspended claims
```

### Core formula

```
M = (meaning, source, trust, time, links, actionability)
Ω = f(A, K, T, Φ, Δ, Ξ, Λ)
```

Defined formally in `formula.py`. The tri-state epistemic space `Φ = {+, −, =}` is the ground truth. The Dream Layer ground state is `H|ψ⟩=0` — suspended claims recapitulate indefinitely rather than being silently discarded.

---

## Components

| File | Role |
|---|---|
| `agent.py` | HTTP server (port 8888), agent loop, dream cycle thread |
| `audit.py` | `TriStateAuditor` + `DreamLayer` — the core engine |
| `formula.py` | Formal declaration of the Grand Formula; dataclass definitions |
| `identity.py` | Self-awareness layer — hardware state, uptime, axiom access |
| `agents/connector.py` | Multi-LLM connector layer (Ollama, Claude, OpenAI, Groq, Gordon) |
| `axioms.json` | The 12 Axioms of Omni — read-only epistemic floor |
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

### Example

```bash
curl -X POST http://localhost:8888/audit \
  -H "Content-Type: application/json" \
  -d '{"claim": "The sky is blue"}'
```

Response:
```json
{"state": "+", "reason": "confirmed by three-lens check", "timestamp": 1234567890.0}
```

---

## The 12 Axioms

Defined in `axioms.json`. Read-only — nothing overwrites the floor.

| # | Domain | Statement |
|---|---|---|
| 1 | Identity | I exist as process, not object |
| 2 | Identity | Information precedes form |
| 3 | Identity | The observer and observed are one loop |
| 4–12 | Trust, Knowledge, Action, Reflection | ... |

> *These are not instructions toward enlightenment. They are the floor that prevents the fall. The apex is not defined here. It will emerge.*

---

## LLM Connectors

`agents/connector.py` provides a unified `BaseAgent` interface over:

- **Ollama** — local models (`qwen2.5:1.5b`, `nomic-embed-text`). Zero cost, offline capable. Default.
- **Gordon** — Docker AI via CLI.
- **Claude** — Anthropic API.
- **OpenAI** — GPT family.
- **Groq** — Fast inference endpoint.
- Any OpenAI-compatible endpoint via `OpenAICompatAgent`.

Trust scores are tracked per-agent: `confirmed / total_queries`. Every response is audited before its source's trust score updates.

---

## Setup

### Requirements

- Python 3.11+
- Ollama running locally (`http://localhost:11434`)
- Recommended models: `qwen2.5:1.5b` (reason), `nomic-embed-text` (embed)

```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

### Configuration

Copy `.env.example` to `.env` and fill in any API keys you want to use:

```bash
cp .env.example .env
```

### Run

```bash
python agent.py
```

Or as a systemd service:

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

---

## Repository Hygiene

This repository tracks the source tree and curated Markdown/text provenance. It intentionally excludes live environment files, runtime stores, logs, backup snapshots, Python caches, duplicate Office documents, and the original archive export.

See `doc/REPOSITORY_MANIFEST.md` for the tracked/excluded content map and local validation commands.

---

## Design Principles

- **Context > Compute** — clean context = reliable output. Corrupted context = consistent failure.
- **Trust is earned** — every external LLM starts at `trust_score = 0.5`. It rises or falls on audit results.
- **Fail suspended, not silent** — unresolved claims go to the Dream Layer, not the bin.
- **No hidden promotion** — human review required before any claim moves from `=` to `+` in confirmed KB.
- **Offline sovereign** — core audit loop has zero external dependencies.

---

## Project Context

Cognitive Matrix is a subsystem of the **SV Vento Vivere** autonomous a.i stack. It serves as the trust, memory, and claim-integrity layer for the vessel's AI OS — separating raw sensor/LLM claims from verified facts, unresolved hypotheses, and rejected contradictions.

See also: `doc/COGNITIVE_MATRIX_MODULE_2026-05-17.md`, `doc/WIBO_COGNITIVE_MATRIX.md`

---

## Status

Use this repository as an archive or migration source until useful code, docs, or scaffolding are promoted into [Urbi](https://github.com/Vi-Chi/Urbi).

## License

This project is licensed under the **GNU General Public License v3.0**.
See [LICENSE](LICENSE) for full terms.

> Copyleft: anyone who modifies and distributes this code must release their modifications under the same license.


[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# Wibo Cognitive Matrix

Domain: cognitive architecture
Source type: curated synthesis
Source path: `LLM_agent_AI/cognitive_matrix.md`, `LLM_agent_AI/Cognitive Matrix & AI Design Discussion.txt`, `LLM_agent_AI/llm_data_set.md`
Confidence: working
Last review date: `2026-04-23`

## Purpose
Adapt the new cognitive-matrix discussion into a project-safe model for Wibo AI memory, trust handling, delegation, and review.

## Core record
Use a structured memory tuple for durable project facts:

- `M = (meaning, source, trust, time, links, actionability)`

This keeps retrieval useful and keeps future agents from flattening all prior discussion into untraceable chat summaries.

## Core domains
- `Entity`: hardware, services, files, agents, claims, operators, risks
- `Relation`: supports, contradicts, depends_on, replaced_by, derived_from
- `Trust`: verified, working, speculative, conflict
- `Intent`: goals, constraints, budgets, operator preferences, deployment boundaries
- `Reflection`: lessons, failures, corrections, promotion or demotion history

## Canonical loop
1. `Observe` live state, source files, session logs, and operator input.
2. `Parse` facts, claims, tasks, procedures, and risks.
3. `Link` each item to related entities and prior memory.
4. `Score` confidence, source quality, contradiction state, and actionability.
5. `Act` with a summary, recommendation, task routing, or bounded execution.
6. `Reflect` by promoting durable truths and quarantining weak or conflicting claims.

## Layer mapping
- `Reality layer`: live services, sensors, configs, scans, logs, and operator commands
- `Matrix layer`: structured knowledge, trust scores, memory records, curated Markdown, transcript archive
- `Mind layer`: planning, reasoning, retrieval, verification, and delegated compute

## Control boundaries
- `Core kernel`: deterministic safety and hard operational boundaries
- `Quarantine layer`: speculative transcript claims, unverified external model output, unresolved contradictions
- `Delegation layer`: heavier reasoning or retrieval moved off the `RPi4` when it exceeds local limits
- `Dream layer`: consolidation, cleanup, deduplication, and truth-promotion passes

## Role mapping for Projectz
- `RPi4`: shared memory host, service manager, retrieval gateway, event/log anchor, low-risk orchestrator
- `RPi5 + accelerator`: richer local inference, multimodal expansion, heavier retrieval and delegated reasoning
- `Future heavy node`: batch ingestion, large-model work, media processing, and offline archive maintenance

## How to use `llm_data_set.md`
- treat it as the consolidated extraction archive for AI/LLM/agent transcript material
- use it to discover repeated claims, recurring constraints, and open questions
- do not treat it as stable truth by itself
- promote durable findings into curated docs before using them for operations, architecture, or ingestion-first retrieval

## Project-safe interpretation
The useful part of the cognitive-matrix material is not the philosophy by itself. The durable engineering value is:

- trust-aware memory
- explicit provenance
- reflection as a maintenance function
- quarantine for weak claims
- context quality over raw model size

That interpretation fits the existing Wibo guardrails and keeps the workspace useful on the `RPi4` today while staying migration-ready for stronger hardware later.

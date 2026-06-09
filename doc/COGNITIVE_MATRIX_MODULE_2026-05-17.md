# Cognitive Matrix Module - 2026-05-17

Status: canonical summary from `!Modules/Cognitive_Matrix_Module`
Confidence: working prototype

## Source Files

- `!Modules/Cognitive_Matrix_Module/cognitive_matrix.md`
- `!Modules/Cognitive_Matrix_Module/audit.py`
- `!Modules/Cognitive_Matrix_Module/context_store.json`

## Identity

The Cognitive Matrix is a trust, memory, and claim-integrity layer for the Projectz / Wibo knowledge system. It is intended to separate raw claims from supported facts, unresolved ideas, and rejected contradictions.

It is not a shell executor, service manager, navigation controller, or secret store.

## Core Model

The design note defines a matrix record as:

```text
M = (meaning, source, trust, time, links, actionability)
```

The recurring architecture is:

| Domain | Purpose |
|---|---|
| Entity | concepts, people, sources, claims, tasks |
| Relation | supports, contradicts, depends on, links |
| Trust | reliability, bias, evidence, uncertainty |
| Intent | goals, constraints, priorities |
| Reflection | lessons, failures, dream-layer consolidation |

## Prototype Code Findings

`audit.py` contains two main classes:

| Class | Role |
|---|---|
| `TriStateAuditor` | audits a claim against live context and stored claims |
| `DreamLayer` | queues unresolved claims and retries them later |

The auditor returns:

| State | Meaning | KB behavior |
|---|---|---|
| `+` | supported enough to surface | cite source and use within scope |
| `-` | contradicted or unsafe | reject or quarantine |
| `=` | unresolved | hold for review/dream layer |

The code checks for direct contradiction, weak contextual support, overconfident wording, internal self-conflict, ambiguity, and a three-lens consistency pattern.

## Safety Notes

- Running `audit.py` interactively appends to `context_store.json`.
- The store is a simple local JSON file, not an authoritative database.
- It should not be connected to RAG promotion or service action until test fixtures, source attribution, and rollback behavior exist.
- It should never store raw secrets or copied credentials.

## Recommended Integration

1. Use the tri-state model in KB reports and review queues.
2. Keep human review over any claim promotion from `=` to `+`.
3. Link claims to exact source paths and dates.
4. Treat vendor/model/service claims as `=` until verified against current live or official sources.
5. Keep Cognitive Matrix as policy context for AnythingLLM/Codex, not an autonomous operator.

## Promotion Decision

Promote the concept and prototype summary into the KB. Keep the raw `context_store.json` and interactive code review-first unless a future task explicitly turns them into a tested library or ingestion helper.
